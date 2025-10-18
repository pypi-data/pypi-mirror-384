# src/fppull/cli/detect_latest_week.py
import os
import sys
import requests
from dotenv import load_dotenv


def main() -> int:
    load_dotenv()
    league = os.getenv("LEAGUE_ID")
    season = os.getenv("SEASON")
    swid = (os.getenv("SWID") or "").strip()
    s2 = (os.getenv("ESPN_S2") or os.getenv("espn_s2") or "").strip()

    if not (league and season and swid and s2):
        print("Missing LEAGUE_ID/SEASON or cookies in env", file=sys.stderr)
        return 2

    # SWID must include braces and be quoted in the Cookie header
    swid_fmt = swid if swid.startswith("{") else "{" + swid.strip("{}") + "}"
    cookie = f'SWID="{swid_fmt}"; espn_s2={s2}'

    base = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={league}",
        "Cookie": cookie,
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Platform": "kona-PROD",
    }

    try:
        r = requests.get(base, params={"view": "mStatus"}, headers=headers, timeout=20)
        r.raise_for_status()
        j = r.json()
        status = j.get("status", {})
        latest = (
            status.get("scoringPeriodId") or status.get("currentMatchupPeriod") or 0
        )
        print(int(latest))
        return 0
    except requests.HTTPError as e:
        print(
            f"HTTP {e.response.status_code if e.response else '?'}: {getattr(e.response,'text','')[:200]}",
            file=sys.stderr,
        )
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
