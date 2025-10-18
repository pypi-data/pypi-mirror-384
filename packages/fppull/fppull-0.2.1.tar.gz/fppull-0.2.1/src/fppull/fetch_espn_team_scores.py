# src/fppull/fetch_espn_team_scores.py
import argparse
import contextlib
import json
import json as _json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# --- add near imports ---
class AuthError(RuntimeError): ...


class RedirectError(RuntimeError): ...


class NonJSONError(RuntimeError): ...


class NetError(RuntimeError): ...


class HttpError(RuntimeError): ...


# Central exit codes (top-level module constants)
EXIT_OK = 0
EXIT_EMPTY = 2  # already used with --fail-on-empty
EXIT_CONFIG = 10
EXIT_AUTH = 11
EXIT_REDIRECT = 12
EXIT_NONJSON = 13
EXIT_HTTP = 14
EXIT_NET = 15
EXIT_SCHEMA = 16

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"

# -----------------------------------------------------------------------------
# ESPN READS API HELPERS
# -----------------------------------------------------------------------------
READS_BASE_TMPL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    "seasons/{season}/segments/0/leagues/{league_id}"
)

_LOG_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}


def _ts() -> str:
    # UTC timestamp for consistent ordering in CI logs
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _level_num(level: str) -> int:
    return _LOG_LEVELS.get(level.upper(), 20)


def _emit_keyval(level: str, event: str, **fields: object) -> None:
    parts = [
        f"time={_ts()}",
        f"level={level}",
        f"event={event}",
        "mod=fetch_espn_team_scores",
    ]
    for k, v in fields.items():
        if v is None:
            continue
        s = str(v).replace("\n", " ").strip()
        parts.append(f"{k}={s}")
    sys.stderr.write(" ".join(parts) + "\n")


def _emit_json(level: str, event: str, **fields: object) -> None:
    payload = {
        "time": _ts(),
        "level": level,
        "event": event,
        "mod": "fetch_espn_team_scores",
    }
    for k, v in fields.items():
        if v is None:
            continue
        payload[k] = v
    # Compact JSON to keep it grep/line friendly
    sys.stderr.write(_json.dumps(payload, separators=(",", ":")) + "\n")


# Defaults; overridden by CLI/env later
_LOG_THRESHOLD = _level_num(os.getenv("LOG_LEVEL", "INFO"))
_LOG_FORMAT = os.getenv("LOG_FORMAT", "KEYVAL").upper()  # KEYVAL or JSON


def _log(level: str, event: str, **fields: object) -> None:
    if _level_num(level) < _LOG_THRESHOLD:
        return
    if _LOG_FORMAT == "JSON":
        _emit_json(level, event, **fields)
    else:
        _emit_keyval(level, event, **fields)


def log_debug(event: str, **fields: object) -> None:
    _log("DEBUG", event, **fields)


def log_info(event: str, **fields: object) -> None:
    _log("INFO", event, **fields)


def log_warn(event: str, **fields: object) -> None:
    _log("WARN", event, **fields)


def log_error(event: str, **fields: object) -> None:
    _log("ERROR", event, **fields)


# ---------------------------------------------------------------------------


def _league_api_base() -> str:
    """Base URL for ESPN Fantasy 'reads' API."""
    season = os.getenv("SEASON", "").strip()
    league_id = os.getenv("LEAGUE_ID", "").strip()
    if not season or not league_id:
        raise SystemExit("Set SEASON and LEAGUE_ID in .env")
    return READS_BASE_TMPL.format(season=season, league_id=league_id)


def _cookie_from_file(path: str) -> str | None:
    """Read a one-line cookie file that contains 'SWID=...; espn_s2=...'."""
    p = Path(path)
    if not p.is_file():
        return None
    with contextlib.suppress(Exception):
        txt = p.read_text(encoding="utf-8").strip()
        # Quick sanity: must include at least one expected cookie key
        if "SWID=" in txt or "espn_s2=" in txt:
            return txt
    return None


def _auth_headers() -> dict[str, str]:
    """
    Build headers/cookies so ESPN accepts requests.
    Priority:
      1) COOKIE_FILE (if provided and readable)
      2) SWID + espn_s2 from .env
    """
    cookie_header = None

    cookie_file = os.getenv("COOKIE_FILE", "").strip()
    if cookie_file:
        cookie_header = _cookie_from_file(cookie_file)

    if not cookie_header:
        swid = os.getenv("SWID", "").strip()
        s2 = os.getenv("ESPN_S2", "").strip()
        parts = []
        if swid:
            parts.append(f"SWID={swid}")  # include braces
        if s2:
            parts.append(f"espn_s2={s2}")
        cookie_header = "; ".join(parts) if parts else None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={os.getenv('LEAGUE_ID','')}",
    }
    if cookie_header:
        headers["Cookie"] = cookie_header
    return headers


# -----------------------------------------------------------------------------
# HTTP session with retries (CIP-2)
# -----------------------------------------------------------------------------
_session: requests.Session | None = None


def _int_env(name: str, default: int) -> int:
    try:
        v = int(os.getenv(name, "").strip() or default)
        return v if v >= 0 else default
    except Exception:
        return default


def _float_env(name: str, default: float) -> float:
    try:
        v = float(os.getenv(name, "").strip() or default)
        return v if v >= 0 else default
    except Exception:
        return default


def _http_session() -> requests.Session:
    """
    Singleton requests.Session configured with retries + backoff.
    Retries: 429, 5xx; GET only; honors Retry-After; exponential backoff.
    """
    global _session
    if _session is not None:
        return _session

    # Tunables (env with safe defaults)
    total = _int_env("HTTP_RETRIES", 5)
    connect = _int_env("HTTP_CONNECT_RETRIES", 3)
    read = _int_env("HTTP_READ_RETRIES", 3)
    status = _int_env("HTTP_STATUS_RETRIES", 5)
    backoff = _float_env("HTTP_BACKOFF", 0.5)
    pool = _int_env("HTTP_POOL", 20)

    retry = Retry(
        total=total,
        connect=connect,
        read=read,
        status=status,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry, pool_connections=pool, pool_maxsize=pool)
    s = requests.Session()
    # Mount for all HTTPS (covers lm-api-reads.fantasy.espn.com)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    _session = s

    # one-shot visibility of HTTP tunables
    log_debug(
        "http.session_ready",
        retries_total=total,
        retries_connect=connect,
        retries_read=read,
        retries_status=status,
        backoff=backoff,
        pool=pool,
        timeout_default=_float_env("HTTP_TIMEOUT", 30.0),
    )

    return s


def _get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        s = _http_session()
        _params = params or {}
        _start = datetime.now(UTC)
        r = s.get(
            url,
            params=_params,
            headers=_auth_headers(),
            timeout=_float_env("HTTP_TIMEOUT", 30.0),
            allow_redirects=False,
        )
        _lat_ms = int((datetime.now(UTC) - _start).total_seconds() * 1000)
        # Minimal debug for observability (no secrets in params here)
        log_debug(
            "http.response",
            status=r.status_code,
            ms=_lat_ms,
            view=_params.get("view"),
            spid=_params.get("scoringPeriodId"),
            mpid=_params.get("matchupPeriodId"),
        )
    except requests.exceptions.RequestException as e:
        raise NetError(f"Network error: {e}") from e

    status = r.status_code
    ctype = r.headers.get("Content-Type", "")

    if status in (301, 302, 303, 307, 308):
        loc = r.headers.get("Location", "")
        raise RedirectError(f"Redirected ({status}) to {loc}")
    if status in (401, 403):
        raise AuthError(
            f"{status} Unauthorized/Forbidden — check SWID/espn_s2 cookies (not expired)"
        )
    if "application/json" not in ctype:
        preview = (r.text or "")[:300].replace("\n", " ")
        raise NonJSONError(f"Non-JSON response ({ctype}). Preview: {preview}")

    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise HttpError(f"HTTP {status}: {e}") from e

    try:
        return r.json()
    except ValueError as e:
        raise NonJSONError(f"Invalid JSON payload: {e}") from e


def _detect_current_week(base_url: str) -> int:
    """
    Ask ESPN for the league settings to detect the 'current' week.
    Prefers mSettings.status.currentMatchupPeriod, with fallbacks.
    """
    try:
        league = _get_json(base_url, params={"view": "mSettings"})
        status = league.get("status", {}) if isinstance(league, dict) else {}
        for v in (
            status.get("currentMatchupPeriod"),
            status.get("latestScoringPeriod"),
            league.get("scoringPeriodId"),
        ):
            if isinstance(v, int) and v >= 1:
                return v
            try:
                iv = int(v)
                if iv >= 1:
                    return iv
            except Exception:
                pass
    except Exception:
        pass
    # Final fallback
    try:
        return max(1, int(os.getenv("CURRENT_WEEK", "1")))
    except Exception:
        return 1


def _resolve_weeks(weeks_raw: str, base_url: str) -> list[int]:
    """
    Turn WEEKS env into a concrete list of ints.
    - If blank or 'ALL': use weeks 1..current_week (auto-detected).
    - Else: parse comma-separated list.
    """
    weeks_raw = (weeks_raw or "").strip()
    if not weeks_raw or weeks_raw.upper() == "ALL":
        current_week = _detect_current_week(base_url)
        if current_week < 1:
            raise SystemExit("Could not auto-detect CURRENT_WEEK from ESPN.")
        return list(range(1, current_week + 1))
    try:
        weeks = [int(w) for w in weeks_raw.split(",") if w.strip()]
    except ValueError:
        raise SystemExit(
            "WEEKS must be 'ALL' (or blank) or a comma list of integers (e.g., '1,2,3')."
        ) from None
    if not weeks:
        raise SystemExit("WEEKS list parsed empty — check your .env value.")
    return weeks


# -----------------------------------------------------------------------------
# Extraction helpers
# -----------------------------------------------------------------------------
def _coerce_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _extract_points_from_team_obj(team_obj: dict[str, Any]) -> float | None:
    """
    ESPN has varied where the numeric ‘official’ points live.
    Try a series of common locations and return the first numeric found.
    """
    # Direct fields
    for k in ("totalPoints", "appliedStatTotal", "points", "score"):
        v = _coerce_float(team_obj.get(k))
        if v is not None:
            return v

    # Nested candidates
    nested_candidates = [
        ("cumulativeScore", "score"),
        ("rosterForCurrentScoringPeriod", "appliedStatTotal"),
        ("totalPointsLive", None),
        ("adjustment", "points"),
    ]
    for a, b in nested_candidates:
        inner = team_obj.get(a)
        if isinstance(inner, dict):
            v = inner.get(b) if b else inner
            fv = _coerce_float(v)
            if fv is not None:
                return fv

    # Some payloads store totals per period keyed by IDs; sum if found
    for key in ("appliedStatTotalByScoringPeriod", "pointsByScoringPeriod"):
        by_period = team_obj.get(key)
        if isinstance(by_period, dict):
            try:
                return float(sum(_coerce_float(v) or 0.0 for v in by_period.values()))
            except Exception:
                pass

    return None


def _rows_from_schedule_obj(obj: dict[str, Any]) -> list[tuple[int, float]]:
    """
    Return list of (teamId, officialPoints) for this matchup object.
    Handles both legacy 'teams' array and new 'home'/'away' objects.
    """
    rows: list[tuple[int, float]] = []

    # Legacy shape
    if "teams" in obj and isinstance(obj["teams"], list) and obj["teams"]:
        for t in obj["teams"]:
            tid = t.get("teamId")
            pts = _extract_points_from_team_obj(t)
            if tid is not None and pts is not None:
                rows.append((int(tid), float(pts)))
        return rows

    # Newer shape: 'home' and 'away'
    for side in ("home", "away"):
        side_obj = obj.get(side)
        if isinstance(side_obj, dict):
            tid = side_obj.get("teamId")
            pts = _extract_points_from_team_obj(side_obj)
            if tid is not None and pts is not None:
                rows.append((int(tid), float(pts)))

    return rows


# Add this helper near your other helpers (module level).
def _is_for_week(obj: dict[str, Any], wk: int) -> bool:
    """
    True if this schedule object corresponds to the requested fantasy week.
    We accept either matchupPeriodId or scoringPeriodId matching wk.
    """
    try:
        if int(obj.get("matchupPeriodId", -1)) == int(wk):
            return True
    except Exception:
        pass
    try:
        if int(obj.get("scoringPeriodId", -1)) == int(wk):
            return True
    except Exception:
        pass
    return False


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():

    # [CIP-1 B] — at the top of main(), before reading env
    def _build_cli() -> argparse.Namespace:
        p = argparse.ArgumentParser(
            description="Fetch ESPN official team scores per week."
        )
        p.add_argument(
            "--weeks",
            type=str,
            default=None,
            help="Comma list (e.g. '1,2,3') or 'ALL'. Overrides WEEKS env.",
        )
        p.add_argument(
            "--out",
            type=str,
            default=None,
            help="Override output CSV path. Defaults to processed/season_{SEASON}/espn/team_week_official.csv",
        )
        p.add_argument(
            "--fail-on-empty",
            action="store_true",
            help="Exit with code 2 if no matchup rows were collected.",
        )
        p.add_argument(
            "--log-level",
            type=str,
            default=None,
            choices=["DEBUG", "INFO", "WARN", "ERROR"],
            help="Override LOG_LEVEL env for this run.",
        )
        p.add_argument(
            "--log-format",
            type=str,
            default=None,
            choices=["KEYVAL", "JSON"],
            help="Override LOG_FORMAT env (KEYVAL or JSON).",
        )
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse only; do not write CSV.",
        )
        p.add_argument(
            "--no-raw",
            action="store_true",
            help="Skip writing raw JSON snapshots under data/raw.",
        )
        return p.parse_args()

    # [CIP-1 C] — inside main(), as first lines
    args = _build_cli()
    load_dotenv(ROOT / ".env")

    # Resolve logging overrides (CLI beats env)
    global _LOG_THRESHOLD, _LOG_FORMAT
    if args.log_level:
        _LOG_THRESHOLD = _level_num(args.log_level)
    # re-read env if not overridden by CLI (handles .env)
    if not args.log_level:
        _LOG_THRESHOLD = _level_num(os.getenv("LOG_LEVEL", "INFO"))
    if args.log_format:
        _LOG_FORMAT = args.log_format.upper()
    else:
        _LOG_FORMAT = os.getenv("LOG_FORMAT", "KEYVAL").upper()

    season = os.getenv("SEASON")
    league_id = os.getenv("LEAGUE_ID")
    if not season or not league_id:
        log_error("config.missing_env", missing="SEASON or LEAGUE_ID")
        sys.exit(EXIT_CONFIG)

    # right after arg parsing / env checks in main()
    def _exit_code_for(err: Exception) -> int:
        if isinstance(err, AuthError):
            return EXIT_AUTH
        if isinstance(err, RedirectError):
            return EXIT_REDIRECT
        if isinstance(err, NonJSONError):
            return EXIT_NONJSON
        if isinstance(err, NetError):
            return EXIT_NET
        if isinstance(err, HttpError):
            return EXIT_HTTP
        return EXIT_HTTP  # default bucket

    last_error_code: int | None = None

    base = _league_api_base()
    weeks_env = os.getenv("WEEKS", "")
    weeks = _resolve_weeks(args.weeks if args.weeks is not None else weeks_env, base)
    log_info(
        "run.start", season=season, league_id=league_id, weeks=",".join(map(str, weeks))
    )
    log_info("weeks.resolved", weeks=",".join(map(str, weeks)))

    # Load canonical team names (from league_context)
    teams_csv = PROCESSED / f"season_{season}" / "espn" / "teams.csv"
    team_names: dict[int, str] = {}
    if teams_csv.exists():
        tdf = pd.read_csv(teams_csv)
        # accept "team_name" if present; else try to reconstruct
        name_col = "team_name" if "team_name" in tdf.columns else None
        if not name_col:
            for c in ("teamLocation", "teamNickname"):
                if c not in tdf.columns:
                    tdf[c] = ""
            tdf["team_name"] = (
                tdf.get("teamLocation", "") + " " + tdf.get("teamNickname", "")
            ).str.strip()
            name_col = "team_name"
        for _, r in tdf.iterrows():
            with contextlib.suppress(Exception):
                team_names[int(r["team_id"])] = (
                    str(r[name_col])
                    if pd.notna(r[name_col])
                    else f"Team {int(r['team_id'])}"
                )

    out_rows: list[dict[str, Any]] = []
    raw_dir = RAW / f"season_{season}" / "espn"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for wk in weeks:
        try:
            # First try scoringPeriodId
            data = _get_json(
                base, params={"view": "mMatchupScore", "scoringPeriodId": wk}
            )
            sched = data.get("schedule", [])
            if not isinstance(sched, list):
                sched = []
            # Filter to this week only
            sched = [m for m in sched if _is_for_week(m, wk)]

            # If empty, try matchupPeriodId and filter again
            if not sched:
                data = _get_json(
                    base, params={"view": "mMatchupScore", "matchupPeriodId": wk}
                )
                sched = data.get("schedule", [])
                if not isinstance(sched, list):
                    sched = []
                sched = [m for m in sched if _is_for_week(m, wk)]

            # Save raw for audit/debug (after final fetch)
            if not args.no_raw:
                (raw_dir / f"matchupscore_w{wk:02d}.json").write_text(
                    json.dumps(data, indent=2)
                )
            wk_rows: list[tuple[int, float]] = []
            for m in sched:
                wk_rows.extend(_rows_from_schedule_obj(m))

            if not wk_rows:
                log_warn(
                    "week.empty_rows", week=wk, hint="check cookies or view params"
                )
            else:
                log_info("week.rows_collected", week=wk, rows=len(wk_rows))

            for tid, pts in wk_rows:
                out_rows.append(
                    {
                        "season": int(season),
                        "week": int(wk),
                        "fantasy_team_id": tid,
                        "fantasy_team_name": team_names.get(tid, f"Team {tid}"),
                        "official_pts": round(float(pts), 2),
                    }
                )

        except Exception as e:
            log_error(
                "week.fetch_error",
                week=wk,
                error=e.__class__.__name__,
                detail=str(e)[:300],
            )
            last_error_code = _exit_code_for(e)

    # [CIP-1 E] — enforce deterministic exit on empty, right before early 'return'
    if not out_rows:
        log_error(
            "run.empty_output", hint="double-check cookies and league/week config"
        )
        if args.fail_on_empty:
            sys.exit(EXIT_EMPTY)
        if last_error_code is not None:
            sys.exit(last_error_code)
        return

    CSV_COLUMNS = [
        "season",
        "week",
        "fantasy_team_id",
        "fantasy_team_name",
        "official_pts",
    ]

    def _validate_out_df(df: pd.DataFrame) -> None:
        missing = [c for c in CSV_COLUMNS if c not in df.columns]
        if missing:
            log_error("schema.missing_columns", cols=",".join(missing))
            sys.exit(EXIT_SCHEMA)

        # Type sanity (coerceable checks)
        try:
            bad = []
            for c in ("season", "week", "fantasy_team_id"):
                if (
                    not pd.api.types.is_integer_dtype(df[c])
                    and not pd.to_numeric(df[c], errors="coerce").notna().all()
                ):
                    bad.append(c)

            if (
                not pd.api.types.is_numeric_dtype(df["official_pts"])
                and not pd.to_numeric(df["official_pts"], errors="coerce").notna().all()
            ):
                bad.append("official_pts")
            if bad:
                log_error("schema.type_error", cols=",".join(bad))
                sys.exit(EXIT_SCHEMA)
        except Exception as e:
            log_error("schema.validate_error", detail=str(e)[:300])
            sys.exit(EXIT_SCHEMA)

        # Value sanity
        if not (df["week"] >= 1).all():
            log_error("schema.invalid_week", hint="weeks must be >= 1")
            sys.exit(EXIT_SCHEMA)

    # out_df = pd.DataFrame(out_rows).sort_values(["week", "fantasy_team_id"]).reset_index(drop=True)

    out_df = (
        pd.DataFrame(out_rows, columns=CSV_COLUMNS)
        .sort_values(["week", "fantasy_team_id"])
        .reset_index(drop=True)
    )

    _validate_out_df(out_df)

    if args.dry_run:
        log_info("run.dry_run_no_write", rows=len(out_df))
        return

    # [CIP-1 D] — replace the fixed out_path computation near the end
    default_out = PROCESSED / f"season_{season}" / "espn" / "team_week_official.csv"
    out_path = Path(args.out) if args.out else default_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"✅ Wrote {out_path} with {len(out_df)} rows.")
    log_info("run.wrote_csv", path=str(out_path), rows=len(out_df))
    log_info("run.finish", rows=len(out_df), out=str(out_path))


if __name__ == "__main__":
    main()
