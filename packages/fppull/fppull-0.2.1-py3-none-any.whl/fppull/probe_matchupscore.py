# src/fppull/probe_matchupscore.py
import json
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROC_DIR = ROOT / "data" / "processed"

READS_BASE_TMPL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    "seasons/{season}/segments/0/leagues/{league_id}"
)


def _league_reads_base() -> str:
    season = os.getenv("SEASON", "").strip()
    league_id = os.getenv("LEAGUE_ID", "").strip()
    if not season or not league_id:
        raise SystemExit("Set SEASON and LEAGUE_ID in .env")
    return READS_BASE_TMPL.format(season=season, league_id=league_id)


def _cookie_from_file(path: str) -> str | None:
    try:
        txt = Path(path).read_text(encoding="utf-8").strip()
        # Accept either a whole Cookie: line OR "SWID=...; espn_s2=..."
        if "SWID=" in txt or "espn_s2=" in txt:
            # If the file includes "Cookie:", keep only the value
            return txt.replace("Cookie:", "").strip()
    except Exception:
        pass
    return None


def _auth_headers() -> dict[str, str]:
    cookie_header = None
    cookie_file = os.getenv("COOKIE_FILE", "").strip()
    if cookie_file:
        cookie_header = _cookie_from_file(cookie_file)

    if not cookie_header:
        swid = os.getenv("SWID", "").strip()
        s2 = os.getenv("ESPN_S2", "").strip()
        parts = []
        if swid:
            parts.append(f"SWID={swid}")
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


def _get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    r = requests.get(
        url, params=params, headers=_auth_headers(), timeout=30, allow_redirects=False
    )
    status = r.status_code
    if status in (301, 302, 303, 307, 308):
        loc = r.headers.get("Location", "")
        raise requests.HTTPError(f"Redirected ({status}) to {loc}")
    if status == 403:
        raise requests.HTTPError(
            "403 Forbidden — check SWID/espn_s2 cookies (not expired)"
        )
    ctype = r.headers.get("Content-Type", "")
    if "application/json" not in ctype:
        preview = (r.text or "")[:300].replace("\n", " ")
        raise requests.HTTPError(f"Non-JSON response ({ctype}). Preview: {preview}")
    r.raise_for_status()
    return r.json()


def _team_name_map(base: str) -> dict[int, str]:
    data = _get_json(base, params={"view": "mTeam"})
    m = {}
    for t in data.get("teams", []):
        tid = int(t["id"])
        loc = t.get("location", "") or ""
        nick = t.get("nickname", "") or ""
        name = (f"{loc} {nick}").strip() or t.get("abbrev") or f"Team {tid}"
        m[tid] = name
    return m


def _sum_roster_points(team_obj: dict[str, Any]) -> float:
    # Try appliedStatTotal directly on the roster object if present
    r = team_obj.get("rosterForCurrentScoringPeriod") or {}
    if "appliedStatTotal" in r and isinstance(r["appliedStatTotal"], int | float):
        return float(r["appliedStatTotal"])
    # Otherwise, sum entries
    total = 0.0
    for e in r.get("entries", []) or []:
        p = e.get("playerPoolEntry", {})
        # some payloads put per-entry total under 'appliedStatTotal'
        # sometimes it’s nested under p['appliedStatTotal']
        entry_total = e.get("appliedStatTotal")
        if entry_total is None:
            entry_total = p.get("appliedStatTotal")
        if isinstance(entry_total, int | float):
            total += float(entry_total)
    return total


def main():
    load_dotenv(ROOT / ".env")
    season = os.getenv("SEASON", "").strip()
    league_id = os.getenv("LEAGUE_ID", "").strip()
    week = int(os.getenv("QC_WEEK", os.getenv("QC_WEEK_DEFAULT", "1")).strip() or "1")
    if not season or not league_id:
        print("Need SEASON and LEAGUE_ID in .env", file=sys.stderr)
        sys.exit(1)

    base = _league_reads_base()
    team_names = _team_name_map(base)

    print(f"🔎 Probing mMatchupScore for week {week}")
    data = _get_json(base, params={"view": "mMatchupScore", "scoringPeriodId": week})

    # Save raw JSON for audit
    out_raw = RAW_DIR / f"season_{season}" / "espn"
    out_raw.mkdir(parents=True, exist_ok=True)
    raw_path = out_raw / f"matchupscore_w{week:02d}.json"
    raw_path.write_text(json.dumps(data, indent=2))
    print(f"💾 wrote {raw_path}")

    rows = []
    for sched in data.get("schedule", []):
        for t in sched.get("teams") or []:
            tid = int(t.get("teamId"))
            total_points = t.get("totalPoints")
            if total_points is None:
                total_points = t.get("appliedStatTotal")
            recomputed = _sum_roster_points(t)
            rows.append(
                dict(
                    week=week,
                    team_id=tid,
                    team_name=team_names.get(tid, f"Team {tid}"),
                    api_totalPoints=(
                        float(total_points) if total_points is not None else None
                    ),
                    recomputed_roster_sum=float(recomputed),
                )
            )

    if not rows:
        print("No rows found — this usually means cookies weren’t accepted by ESPN.")
        sys.exit(1)

    df = pd.DataFrame(rows).sort_values(["team_id"]).reset_index(drop=True)
    print(f"\n=== Probe results (week {week}) ===")
    print(df.to_string(index=False))

    # Quick ratios to spot scale issues (e.g., ×3 or ×10)
    def safe_ratio(a, b):
        try:
            return round(a / b, 4) if (a is not None and b and b != 0) else None
        except Exception:
            return None

    df["ratio_api_over_recalc"] = df.apply(
        lambda r: safe_ratio(r["api_totalPoints"], r["recomputed_roster_sum"]), axis=1
    )
    print("\n=== Ratios (api_totalPoints / recomputed_roster_sum) ===")
    print(df[["team_id", "team_name", "ratio_api_over_recalc"]].to_string(index=False))


if __name__ == "__main__":
    main()
