# src/fppull/export_official_scores.py
import argparse
import contextlib
import json
import os
import re
import sys
import time
import typing as T
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

# (keep other imports already present)
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _make_session(league_id: str) -> requests.Session:
    """
    Build a session that looks like a real browser hitting ESPN.
    Includes robust retries and both Cookie header + requests cookies.
    """
    s = requests.Session()

    # Browser-y headers ESPN is happy with
    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://fantasy.espn.com",
            "Referer": f"https://fantasy.espn.com/football/league?leagueId={league_id}",
            "x-fantasy-source": "kona",
            "x-fantasy-platform": "kona",
            "X-Requested-With": "XMLHttpRequest",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Site": "same-origin",
            "DNT": "1",
            "sec-ch-ua": '"Chromium";v="125", "Not.A/Brand";v="24", "Google Chrome";v="125"',
            "sec-ch-ua-platform": '"macOS"',
            "sec-ch-ua-mobile": "?0",
        }
    )

    # Robust retry policy for 403/429/5xx bursts from Akamai/CloudFront
    retry = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=[403, 408, 409, 425, 429, 500, 502, 503, 504],
        allowed_methods={"GET"},
        raise_on_status=False,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s


def _prime_espn_session(
    session: requests.Session, season: str, league_id: str, cookies: dict
) -> None:
    """
    Warm the session using ONLY HTML pages. Do NOT call JSON APIs here.
    """
    ua = session.headers.get("User-Agent", "")
    base_headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # HTML warm-ups (carry cookies; allow redirects)
    session.get(
        "https://www.espn.com/fantasy/",
        headers=base_headers,
        cookies=cookies,
        timeout=30,
        allow_redirects=True,
    )
    time.sleep(0.3)
    session.get(
        "https://fantasy.espn.com/",
        headers=base_headers,
        cookies=cookies,
        timeout=30,
        allow_redirects=True,
    )
    time.sleep(0.3)
    session.get(
        f"https://fantasy.espn.com/football/league?leagueId={league_id}",
        headers=base_headers,
        cookies=cookies,
        timeout=30,
        allow_redirects=True,
    )
    time.sleep(0.8)  # a slightly longer settle time helps


def _extra_html_warmup(
    session: requests.Session, season: str, league_id: str, cookies: dict
) -> None:
    """
    Touch a couple league HTML pages that tend to finalize WAF cookies.
    Keep these as HTML-only hits with redirects allowed.
    """
    ua = session.headers.get("User-Agent", "")
    base_headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={league_id}",
    }
    for u in [
        f"https://fantasy.espn.com/football/league?leagueId={league_id}",
        f"https://fantasy.espn.com/football/scoreboard?leagueId={league_id}",
        f"https://fantasy.espn.com/football/boxscore?leagueId={league_id}",
    ]:
        try:
            session.get(
                u,
                headers=base_headers,
                cookies=cookies,
                timeout=30,
                allow_redirects=True,
            )
            time.sleep(0.25)
        except Exception:
            pass


def _read_cookie_file(path: Path) -> dict[str, str]:
    """
    Read ESPN cookies from a variety of formats and return a dict with keys:
      {"SWID": "...", "ESPN_S2": "..."}

    Supported formats:
      - JSON: {"SWID":"{...}","ESPN_S2":"..."}
      - Simple key=value lines (one per line)
      - semicolon / space separated pairs on a single line: "SWID={...}; espn_s2=..."
      - Netscape cookies.txt columns (domain, flag, path, secure, expiry, name, value)
    The parser is defensive and case-insensitive for 'espn_s2'.
    """
    creds: dict[str, str] = {}
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(
            f"[export_official_scores] Failed reading cookie file {path}: {e}",
            file=sys.stderr,
        )
        return creds

    # 1) Try JSON object first
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            # case variations
            swid = obj.get("SWID") or obj.get("swid")
            s2 = obj.get("ESPN_S2") or obj.get("espn_s2") or obj.get("espnS2")
            if swid:
                creds["SWID"] = str(swid).strip().strip('"').strip("'")
            if s2:
                creds["ESPN_S2"] = str(s2).strip().strip('"').strip("'")
            if {"SWID", "ESPN_S2"}.issubset(creds):
                return creds
    except Exception:
        pass  # not JSON

    # 2) Collect simple key=value from any separators: newline, semicolon, whitespace
    #    This covers "SWID=...; espn_s2=..." and "SWID=...\nespn_s2=..."
    #    We'll split on common separators and also handle quoted values.
    # Regex to find key=value pairs (key: word-like, value: anything non-separator)
    pair_re = re.compile(
        r'(?P<k>SWID|ESPN_S2|espn_s2|espnS2)\s*=\s*(?P<v>\{[^}]*\}|"(?:[^"]*)"|\'(?:[^\']*)\'|[^;\s#]+)',
        re.IGNORECASE,
    )
    for m in pair_re.finditer(raw):
        k = m.group("k").upper()
        v = m.group("v").strip().strip('"').strip("'")
        if k == "ESPN_S2" or k.lower() == "espn_s2" or k == "ESPNS2":
            creds["ESPN_S2"] = v
        elif k == "SWID":
            creds["SWID"] = v

    if {"SWID", "ESPN_S2"}.issubset(creds):
        return creds

    # 3) Try line-by-line key=value parsing (fallback)
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # allow "k=v; k2=v2" on same line: split on ';'
        parts = [p.strip() for p in re.split(r"[;]", s) if p.strip()]
        for p in parts:
            if "=" not in p:
                continue
            k, v = p.split("=", 1)
            k = k.strip().upper()
            v = v.strip().strip('"').strip("'")
            if k in {"SWID", "ESPN_S2"}:
                creds[k] = v
    if {"SWID", "ESPN_S2"}.issubset(creds):
        return creds

    # 4) Try Netscape cookies.txt columns (domain, flag, path, secure, expiry, name, value)
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) >= 7:
            name = parts[-2]
            value = parts[-1]
            if name.upper() == "SWID" and value:
                creds["SWID"] = value.strip()
            elif name.lower() == "espn_s2" and value:
                creds["ESPN_S2"] = value.strip()
    # Done
    return creds


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR_TPL = ROOT / "data" / "processed" / "season_{season}" / "espn"

# REQUIRED_KEYS = ["SEASON", "LEAGUE_ID", "SWID", "ESPN_S2"]
REQUIRED_KEYS = [
    "SEASON",
    "LEAGUE_ID",
]  # SWID/ESPN_S2 are validated with cookie fallback inside _load_env_or_die


def _first(*names: str) -> str | None:
    """Return the first non-empty env value among provided names."""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return None


def _load_env_or_die() -> dict:
    # Load .env from repo root *and* current working dir, last one wins
    load_dotenv(ROOT / ".env", override=False)
    load_dotenv(Path.cwd() / ".env", override=False)

    # Accept common alternate casings/keys
    env = {
        "SEASON": _first("SEASON", "season"),
        "LEAGUE_ID": _first("LEAGUE_ID", "league_id", "LEAGUE", "league"),
        "SWID": _first("SWID", "swid", "ESPN_SWID"),
        "ESPN_S2": _first("ESPN_S2", "espn_s2", "ESPN_S2_TOKEN"),
    }

    # Debug visibility of presence (not values) to make issues obvious
    print(
        "[export_official_scores] env presence:",
        {k: ("set" if bool(v) else "MISSING") for k, v in env.items()},
    )

    # --- COOKIE_FILE fallback when SWID/ESPN_S2 not set in .env
    if not env["SWID"] or not env["ESPN_S2"]:
        cookie_env = _first("COOKIE_FILE", "cookie_file")
        cookie_path = None
        if cookie_env:
            # Try (1) as-given, (2) relative to ROOT, (3) relative to CWD
            cand = [Path(cookie_env), ROOT / cookie_env, Path.cwd() / cookie_env]
            cookie_path = next((p for p in cand if p.exists()), None)

        if cookie_path and cookie_path.exists():
            print(f"[export_official_scores] COOKIE_FILE resolved to: {cookie_path}")
            print(
                f"[export_official_scores] attempting COOKIE_FILE fallback: {cookie_path}"
            )
            creds = _read_cookie_file(cookie_path)
            found_keys = {k for k in ("SWID", "ESPN_S2") if k in creds and creds[k]}
            print(
                f"[export_official_scores] cookie file provided keys: {sorted(found_keys)}"
            )
            if not env["SWID"] and "SWID" in creds:
                env["SWID"] = str(creds["SWID"]).strip().strip('"').strip("'")
            if not env["ESPN_S2"] and "ESPN_S2" in creds:
                env["ESPN_S2"] = str(creds["ESPN_S2"]).strip().strip('"').strip("'")
        else:
            print(
                "[export_official_scores] COOKIE_FILE not found or not set; skipping fallback."
            )

    # Required: season + league
    missing_core = [k for k in ("SEASON", "LEAGUE_ID") if not env.get(k)]
    if missing_core:
        print(f"Missing in environment: {', '.join(missing_core)}", file=sys.stderr)
        print("Ensure .env has lines like:", file=sys.stderr)
        print("  SEASON=2025", file=sys.stderr)
        print("  LEAGUE_ID=123456", file=sys.stderr)
        sys.exit(2)

    # Required for private/official pulls: SWID/ESPN_S2 (from .env or cookie file)
    if not env["SWID"] or not env["ESPN_S2"]:
        print(
            "[export_official_scores] Missing auth cookies. Provide SWID/ESPN_S2 in .env or COOKIE_FILE.",
            file=sys.stderr,
        )
        print("Examples:", file=sys.stderr)
        print("  # .env", file=sys.stderr)
        print("  COOKIE_FILE=secrets/espn.cookie", file=sys.stderr)
        print("  (optional) SWID={...}", file=sys.stderr)
        print("  (optional) ESPN_S2=...", file=sys.stderr)
        print("  # secrets/espn.cookie", file=sys.stderr)
        print("  SWID={...}", file=sys.stderr)
        print("  ESPN_S2=...", file=sys.stderr)
        sys.exit(2)

    return env


def _req(
    session: requests.Session,
    url: str,
    cookies: dict,
    params: dict | list[tuple] | None = None,
    use_cookie_header: bool = False,
    follow_redirects: bool = False,
) -> dict:
    """
    API GET only. If use_cookie_header=True, send cookies via an explicit
    Cookie header; otherwise rely on the session's cookie jar.
    If follow_redirects=False (default), we surface 30x instead of landing on HTML.
    """
    # Normalize ?view=mX&view=mY into a flat list of tuples without mutating caller input
    flat_params: list[tuple[str, T.Any]] = []
    if params is None:
        pass
    elif isinstance(params, dict):
        for k, v in params.items():
            if k == "view" and isinstance(v, list | tuple):
                for vv in v:
                    flat_params.append(("view", vv))
            else:
                flat_params.append((k, v))
    elif isinstance(params, list | tuple):
        for item in params:
            if isinstance(item, list | tuple) and len(item) == 2:
                flat_params.append((str(item[0]), item[1]))
    else:
        raise TypeError(f"Unsupported params type: {type(params)}")

    # derive league id for referer (do not mutate cookies)
    ref_league = ""
    try:
        q = parse_qs(urlparse(url).query)
        ref_league = (q.get("leagueId") or [""])[0]
    except Exception:
        pass
    if not ref_league:
        ref_league = str(cookies.get("LEAGUE_ID", ""))

    headers = {
        "User-Agent": session.headers.get("User-Agent", ""),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={ref_league}",
        "x-fantasy-source": "kona",
        "x-fantasy-platform": "kona",
        "X-Requested-With": "XMLHttpRequest",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    cookie_header = f"SWID={cookies.get('SWID','')}; espn_s2={cookies.get('espn_s2') or cookies.get('ESPN_S2','')}"
    hdrs = dict(headers)
    kw: dict[str, T.Any] = {}
    if use_cookie_header:
        hdrs["Cookie"] = cookie_header
        kw["cookies"] = None
    else:
        kw["cookies"] = cookies

    r = session.get(
        url,
        headers=hdrs,
        params=flat_params,
        timeout=30,
        allow_redirects=bool(follow_redirects),
        **kw,
    )

    # Surface redirects explicitly
    if 300 <= r.status_code < 400:
        loc = r.headers.get("Location")
        print(
            f"[export_official_scores] Redirect {r.status_code} -> {loc}",
            file=sys.stderr,
        )
        raise RuntimeError("ESPN redirected our JSON request (likely auth/waf).")

    ct = (r.headers.get("Content-Type") or "").lower()
    if not ct.startswith("application/json"):
        # Save snapshot for inspection
        dbg_dir = ROOT / "data" / "debug"
        dbg_dir.mkdir(parents=True, exist_ok=True)
        snap = dbg_dir / "espn_block_snapshot.html"
        with contextlib.suppress(Exception):
            snap.write_text(r.text, encoding="utf-8")
        print(
            f"[export_official_scores] Non-JSON response. Saved snapshot: {snap}",
            file=sys.stderr,
        )
        print(f"[export_official_scores] URL: {r.url}", file=sys.stderr)
        print(
            f"[export_official_scores] Content-Type: {r.headers.get('Content-Type')}",
            file=sys.stderr,
        )
        raise RuntimeError("ESPN returned non-JSON to a JSON endpoint.")

    if r.status_code >= 400:
        try:
            r.raise_for_status()
        except Exception as e:
            print(f"HTTP error on {url}: {e}", file=sys.stderr)
            print("Response snippet:", r.text[:800], file=sys.stderr)
            raise

    return r.json()


def _check_login(
    session: requests.Session, season: str, league_id: str, cookies: dict
) -> bool:
    """
    Probe ESPN JSON API with browser-like patterns:
      1) Try cookie-jar auth first, then explicit Cookie header
      2) Try both hosts: lm-api-reads and fantasy
    """
    bases = [
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}",
        f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}",
    ]

    for base in bases:
        # 1) session jar
        try:
            _ = _req(
                session,
                base,
                cookies,
                params=[("view", "mSettings"), ("view", "mTeam")],
                use_cookie_header=False,
                follow_redirects=False,
            )
            print(f"[login_check] probe OK (jar): {base}")
            return True
        except Exception as e:
            print(f"[login_check] probe failed (jar): {e}")

        # 2) explicit Cookie header
        try:
            _ = _req(
                session,
                base,
                cookies,
                params=[("view", "mSettings"), ("view", "mTeam")],
                use_cookie_header=True,
                follow_redirects=False,
            )
            print(f"[login_check] probe OK (header): {base}")
            return True
        except Exception as e:
            print(f"[login_check] probe failed (header): {e}")

    return False


def _team_display_name(t: dict) -> str:
    loc = (t.get("location") or "").strip()
    nick = (t.get("nickname") or "").strip()
    if loc or nick:
        return f"{loc} {nick}".strip()
    name = (t.get("name") or "").strip() or (t.get("abbrev") or "").strip()
    if name:
        return name
    tid = t.get("id")
    return "UNROSTERED" if tid == 0 else f"Team {tid}"


def _collect_matchups(
    session: requests.Session, season: str, league_id: str, cookies: dict
) -> pd.DataFrame:
    """
    Pull schedule + team metadata and return a normalized DataFrame with one row
    per (team, week): week, fantasy_team_id, fantasy_team_name, official_pts
    """
    read_host = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
    classic = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"

    data: dict | None = None

    # Try in order: read host (jar), read host (header), classic (jar), classic (header)
    for base, via_header in (
        (read_host, False),
        (read_host, True),
        (classic, False),
        (classic, True),
    ):
        try:
            data = _req(
                session,
                base,
                cookies,
                params=[("view", "mMatchup"), ("view", "mTeam")],
                use_cookie_header=via_header,
                follow_redirects=False,
            )
            break
        except Exception:
            data = None

    if data is None:
        raise SystemExit(
            "Failed to retrieve league data from ESPN after multiple attempts."
        )

    teams = {t["id"]: _team_display_name(t) for t in data.get("teams", [])}
    sched = data.get("schedule", [])

    rows: list[dict] = []
    for m in sched:
        wk = m.get("matchupPeriodId")
        home = m.get("home") or {}
        away = m.get("away") or {}
        for side in (home, away):
            tid = side.get("teamId")
            if tid is None:
                continue
            rows.append(
                {
                    "week": wk,
                    "fantasy_team_id": tid,
                    "fantasy_team_name": teams.get(
                        tid, "UNROSTERED" if tid == 0 else f"Team {tid}"
                    ),
                    "official_pts": side.get("totalPoints"),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit(
            "Schedule returned 0 rows. Are cookies tied to the right account/league?"
        )

    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
    df["fantasy_team_id"] = pd.to_numeric(
        df["fantasy_team_id"], errors="coerce"
    ).astype("Int64")
    df["official_pts"] = pd.to_numeric(df["official_pts"], errors="coerce")
    return df.sort_values(["week", "fantasy_team_id"])


def _seed_cookies(session: requests.Session, cookies: dict) -> None:
    """Install SWID/espn_s2 into the session for both espn.com and fantasy.espn.com."""
    swid = cookies.get("SWID") or cookies.get("swid")
    s2 = cookies.get("espn_s2") or cookies.get("ESPN_S2") or cookies.get("espnS2")

    # leading-dot (covers subdomains)
    if swid:
        session.cookies.set("SWID", swid, domain=".espn.com", path="/")
        session.cookies.set("SWID", swid, domain=".fantasy.espn.com", path="/")
    if s2:
        session.cookies.set("espn_s2", s2, domain=".espn.com", path="/")
        session.cookies.set("espn_s2", s2, domain=".fantasy.espn.com", path="/")

    # exact hosts (belt-and-suspenders)
    if swid:
        session.cookies.set("SWID", swid, domain="espn.com", path="/")
        session.cookies.set("SWID", swid, domain="fantasy.espn.com", path="/")
    if s2:
        session.cookies.set("espn_s2", s2, domain="espn.com", path="/")
        session.cookies.set("espn_s2", s2, domain="fantasy.espn.com", path="/")


def _normalize_cookies(c: dict) -> dict:
    """
    Ensure cookies have correct keys and decoded values.
    - Keep SWID as-is (braces are fine).
    - URL-decode espn_s2 if it contains percent-encoding.
    """
    swid = (c.get("SWID") or c.get("swid") or "").strip().strip('"').strip("'")
    s2 = (
        (c.get("espn_s2") or c.get("ESPN_S2") or c.get("espnS2") or "")
        .strip()
        .strip('"')
        .strip("'")
    )
    if "%" in s2:
        s2 = unquote(s2)
    return {"SWID": swid, "espn_s2": s2}


def _normalize_scores_df(df: pd.DataFrame, season: int) -> pd.DataFrame:
    """
    Normalize and validate the scoreboard frame:
      - drop rows missing keys
      - enforce dtypes
      - fill team names (incl. UNROSTERED for team_id==0)
      - return canonical column order
    """
    if df.empty:
        return df

    out = df.dropna(subset=["week", "fantasy_team_id", "official_pts"]).copy()
    # fail fast if nothing usable remains after required-field drop
    if out.empty:
        raise SystemExit(
            "No valid rows after normalization (missing week/team/points). "
            "Check cookies, league id/season, or ESPN availability."
        )

    # season & ids
    out["season"] = int(season)
    out["week"] = (
        pd.to_numeric(out["week"], errors="coerce").astype("Int64").astype(int)
    )
    out["fantasy_team_id"] = (
        pd.to_numeric(out["fantasy_team_id"], errors="coerce")
        .astype("Int64")
        .astype(int)
    )

    # names: treat empty as NA, set UNROSTERED for id==0, fallback to "Team {id}"
    if "fantasy_team_name" not in out.columns:
        out["fantasy_team_name"] = pd.NA
    else:
        out["fantasy_team_name"] = out["fantasy_team_name"].replace("", pd.NA)
    # label ESPN's team_id==0 bucket
    unro_mask = out["fantasy_team_id"] == 0
    out.loc[unro_mask, "fantasy_team_name"] = out.loc[
        unro_mask, "fantasy_team_name"
    ].fillna("UNROSTERED")
    miss_mask = out["fantasy_team_name"].isna()
    out.loc[miss_mask, "fantasy_team_name"] = "Team " + out.loc[
        miss_mask, "fantasy_team_id"
    ].astype(int).astype(str)

    # points
    out["official_pts"] = pd.to_numeric(out["official_pts"], errors="coerce").astype(
        float
    )
    # validate: no null points after coercion
    if out["official_pts"].isna().any():
        bad_rows = out.loc[
            out["official_pts"].isna(), ["week", "fantasy_team_id", "fantasy_team_name"]
        ]
        raise SystemExit(
            "Normalization error: {n} row(s) have null official_pts after coercion. "
            "Upstream fetch may be incomplete; re-check cookies/season/week availability. "
            "Examples: {examples}".format(
                n=bad_rows.shape[0],
                examples=bad_rows.head(3).to_dict(orient="records"),
            )
        )

    # validate: no duplicate keys (season, week, team)
    key_cols = ["season", "week", "fantasy_team_id"]
    dup_mask = out.duplicated(key_cols, keep=False)
    if dup_mask.any():
        dups = out.loc[dup_mask, key_cols].sort_values(key_cols).drop_duplicates()
        raise SystemExit(
            f"Normalization error: duplicate rows detected for keys {key_cols}. "
            f"Examples: {dups.head(5).to_dict(orient='records')}"
        )

    # deterministic ordering & clean index for downstream diffs
    out = out.sort_values(["season", "week", "fantasy_team_id"]).reset_index(drop=True)

    # canonical order
    out = out[
        ["season", "week", "fantasy_team_id", "fantasy_team_name", "official_pts"]
    ]
    return out


def _atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    """
    Write CSV atomically to avoid half-written files if a process is interrupted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)


def _write_scoreboards(base_dir: Path, df: pd.DataFrame) -> dict[str, Path]:
    """
    Persist scoreboard CSVs in all schemas our downstream tools expect.
    Returns the written paths for logging or tests.
    """
    out_csv_week = base_dir / "scoreboard_week.csv"
    out_csv_std = base_dir / "scoreboard.csv"
    out_csv_compat = base_dir / "weekly_scores.csv"

    # native schema
    _atomic_write_csv(df, out_csv_week)
    _atomic_write_csv(df, out_csv_std)

    # compatibility schema: season, week, team_id, team_name, points
    df_compat = df.rename(
        columns={
            "fantasy_team_id": "team_id",
            "fantasy_team_name": "team_name",
            "official_pts": "points",
        }
    )[["season", "week", "team_id", "team_name", "points"]]
    _atomic_write_csv(df_compat, out_csv_compat)

    return {
        "scoreboard_week": out_csv_week,
        "scoreboard": out_csv_std,
        "weekly_scores": out_csv_compat,
    }


def _apply_week_filter(
    df: pd.DataFrame, week: int | None = None, week_range: tuple[int, int] | None = None
) -> pd.DataFrame:
    """
    Filter the normalized scoreboard by a single week or an inclusive range.
    Returns the same df if no filter is provided.
    """
    if df.empty or (week is None and week_range is None):
        return df

    if week is not None:
        return df[df["week"] == int(week)].reset_index(drop=True)

    lo, hi = week_range
    if lo > hi:
        lo, hi = hi, lo
    return df[(df["week"] >= int(lo)) & (df["week"] <= int(hi))].reset_index(drop=True)


def main() -> None:
    # CLI: week selector (mutually exclusive single week vs range)
    parser = argparse.ArgumentParser(description="Export ESPN official scores.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--week", type=int, help="Filter to a single week (e.g., --week 5)."
    )
    group.add_argument(
        "--week-range",
        type=str,
        metavar="A-B",
        help="Inclusive week range (e.g., --week-range 3-6).",
    )
    # output + verbosity
    parser.add_argument(
        "--out-dir",
        type=str,
        help="Override output directory (defaults to data/processed/season_{SEASON}/espn).",
    )
    verb = parser.add_mutually_exclusive_group()
    verb.add_argument(
        "--quiet", action="store_true", help="Suppress non-essential logs."
    )
    verb.add_argument("--verbose", action="store_true", help="Extra logs during run.")

    # output control
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Do not write any files; useful for smoke tests or piping.",
    )
    parser.add_argument(
        "--stdout",
        choices=["csv", "json"],
        help="Emit the normalized results to stdout in the given format (csv|json).",
    )
    parser.add_argument(
        "--skip-probe",
        action="store_true",
        help="Skip the auth preflight probe and attempt the fetch anyway.",
    )

    args = parser.parse_args()

    # if not args.skip_probe:
    #     # Pre-flight auth probe...
    #     if not _check_login(session, season, league, cookies):
    #         if chatty:
    #             print("[export_official_scores] initial auth probe failed; retrying after an extra warm-up...")
    #         time.sleep(1.2)
    #         _prime_espn_session(session, season, league, cookies)
    #         _extra_html_warmup(session, season, league, cookies)
    #         time.sleep(0.8)
    #         if not _check_login(session, season, league, cookies):
    #             raise SystemExit(
    #                 "Login/auth probe failed. ESPN returned HTML/redirect for the league API.\n"
    #                 "- Verify SEASON/LEAGUE_ID\n"
    #                 "- Ensure SWID/ESPN_S2 are valid (or COOKIE_FILE resolves)\n"
    #                 "- Try refreshing cookies from a logged-in browser"
    #             )

    # resolve verbosity
    chatty = args.verbose or not args.quiet
    if args.stdout:
        chatty = False  # keep stdout clean for data

    week_arg: int | None = args.week
    week_range_arg: tuple[int, int] | None = None
    if args.week_range:
        m = re.match(r"^\s*(\d+)\s*-\s*(\d+)\s*$", args.week_range)
        if not m:
            raise SystemExit("Invalid --week-range format. Expected A-B (e.g., 3-6).")
        a, b = int(m.group(1)), int(m.group(2))
        week_range_arg = (a, b)

    env = _load_env_or_die()
    season = str(env["SEASON"])
    league = str(env["LEAGUE_ID"])
    cookies = _normalize_cookies({"SWID": env["SWID"], "espn_s2": env["ESPN_S2"]})
    if chatty:
        print(
            f"[export_official_scores] cookie lengths: SWID={len(cookies['SWID'])}, espn_s2={len(cookies['espn_s2'])}"
        )

    session = _make_session(league)  # keep your existing _make_session
    _seed_cookies(session, cookies)
    _prime_espn_session(session, season, league, cookies)
    time.sleep(0.8)  # small cushion before the first JSON API call
    _extra_html_warmup(session, season, league, cookies)
    time.sleep(0.5)

    # Pre-flight auth probe: verify cookies can access JSON API before heavy calls
    if not args.skip_probe:
        if not _check_login(session, season, league, cookies):
            if chatty:
                print(
                    "[export_official_scores] initial auth probe failed; retrying after an extra warm-up..."
                )
            time.sleep(1.2)
            _prime_espn_session(session, season, league, cookies)
            _extra_html_warmup(session, season, league, cookies)
            time.sleep(0.8)
            if not _check_login(session, season, league, cookies):
                raise SystemExit(
                    "Login/auth probe failed. ESPN returned HTML/redirect for the league API.\n"
                    "- Verify SEASON/LEAGUE_ID\n"
                    "- Ensure SWID/ESPN_S2 are valid (or COOKIE_FILE resolves)\n"
                    "- Try refreshing cookies from a logged-in browser"
                )
    else:
        if chatty:
            print("[export_official_scores] auth probe: SKIPPED (--skip-probe)")

    # Pre-flight auth probe: verify cookies can access JSON API before heavy calls
    if not _check_login(session, season, league, cookies):
        if chatty:
            print(
                "[export_official_scores] initial auth probe failed; retrying after an extra warm-up..."
            )
        time.sleep(1.2)
        _prime_espn_session(session, season, league, cookies)
        time.sleep(0.8)
        if not _check_login(session, season, league, cookies):
            raise SystemExit(
                "Login/auth probe failed. ESPN returned HTML/redirect for the league API.\n"
                "- Verify SEASON/LEAGUE_ID\n"
                "- Ensure SWID/ESPN_S2 are valid (or COOKIE_FILE resolves)\n"
                "- Try refreshing cookies from a logged-in browser"
            )
    elif chatty:
        print("[export_official_scores] auth probe: OK")

    out_dir = (
        Path(args.out_dir).expanduser().resolve()
        if args.out_dir
        else Path(str(OUT_DIR_TPL).format(season=season))
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    if chatty:
        print(f"[export_official_scores] out_dir: {out_dir}")

    df = _collect_matchups(session, season, league, cookies)

    df = _normalize_scores_df(df, int(season))
    df = _apply_week_filter(df, week=week_arg, week_range=week_range_arg)

    # If the filter produced an empty frame, fail fast for clear diagnostics
    if df.empty:
        if week_arg is None and week_range_arg is None:
            sel = "--all-weeks"
        elif week_arg is not None:
            sel = f"--week {week_arg}"
        else:
            sel = f"--week-range {week_range_arg[0]}-{week_range_arg[1]}"
        raise SystemExit(
            f"No rows after applying filter {sel}. Check league/season or chosen week(s)."
        )

    if chatty:
        if week_arg is not None:
            print(f"[export_official_scores] filter: --week {week_arg}")
        elif week_range_arg is not None:
            print(
                f"[export_official_scores] filter: --week-range {week_range_arg[0]}-{week_range_arg[1]}"
            )
        else:
            print("[export_official_scores] filter: none (all weeks)")

    if chatty:
        print("[export_official_scores] columns:", list(df.columns))
        print("[export_official_scores] dtypes:\n", df.dtypes.to_string())

    if chatty:
        print(
            f"[export_official_scores] rows: {len(df)} | weeks: {sorted(df['week'].dropna().unique().tolist())}"
        )
        print(df.head(10).to_string(index=False))

    # Emit / persist results
    # 1) optional stdout stream (happens regardless of --no-write)
    if args.stdout == "csv":
        # always normalized schema: season, week, fantasy_team_id, fantasy_team_name, official_pts
        df.to_csv(sys.stdout, index=False)
    elif args.stdout == "json":
        # compact records for piping to jq or Python
        sys.stdout.write(df.to_json(orient="records"))
        sys.stdout.flush()

    # 2) skip filesystem writes if requested
    if args.no_write:
        if chatty:
            print(
                "[export_official_scores] --no-write set; skipping filesystem outputs."
            )
        return

    # 3) persist outputs (atomic writes; native + compatibility schemas)
    written = _write_scoreboards(out_dir, df)
    print(f"✅ Wrote {written['scoreboard_week']}", file=sys.stderr)
    print(f"✅ Wrote {written['scoreboard']}", file=sys.stderr)
    print(f"✅ Wrote {written['weekly_scores']}", file=sys.stderr)


if __name__ == "__main__":
    main()
