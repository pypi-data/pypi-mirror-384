# src/fppull/cli/auth_check.py
import os
import sys
import requests
from dotenv import load_dotenv

READS_BASE_TMPL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    "seasons/{season}/segments/0/leagues/{league_id}"
)


def _cookie_header() -> str:
    swid = (os.getenv("SWID") or "").strip()
    s2 = (os.getenv("ESPN_S2") or os.getenv("espn_s2") or "").strip()
    if not swid or not s2:
        print("❌ Missing SWID/ESPN_S2 in env", file=sys.stderr)
        sys.exit(3)
    # Ensure braces + quotes around SWID; DO NOT decode espn_s2
    if not swid.startswith("{"):
        swid = "{" + swid.strip("{}") + "}"
    return f'SWID="{swid}"; espn_s2={s2}'


def _headers() -> dict:
    h = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0",
        "Origin": "https://fantasy.espn.com",
        "Referer": "https://fantasy.espn.com/",
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Platform": "kona-PROD",
        "Cookie": _cookie_header(),
    }
    return h


def main() -> int:
    load_dotenv()
    league_id = (os.getenv("LEAGUE_ID") or "").strip()
    season = (os.getenv("SEASON") or "").strip()
    if not league_id or not season:
        print("❌ Missing LEAGUE_ID/SEASON", file=sys.stderr)
        return 2

    url = READS_BASE_TMPL.format(season=season, league_id=league_id)
    params = [("view", "mSettings")]
    try:
        r = requests.get(
            url, params=params, headers=_headers(), timeout=20, allow_redirects=False
        )
    except requests.RequestException as e:
        print(f"🌐 Network error: {e}", file=sys.stderr)
        return 4

    dbg = os.getenv("FPPULL_DEBUG")
    if dbg:
        masked = _headers()["Cookie"]
        s2 = os.getenv("ESPN_S2") or os.getenv("espn_s2") or ""
        if s2:
            masked = masked.replace(s2, (s2[:6] + "…****"))
        print(f"→ GET {url} params={dict(params)}", file=sys.stderr)
        print(f"→ status {r.status_code}", file=sys.stderr)

    # Clear outcomes
    if r.status_code == 200 and r.headers.get("Content-Type", "").startswith(
        "application/json"
    ):
        print("✅ auth OK")
        return 0

    if r.status_code in (301, 302, 303, 307, 308):
        loc = r.headers.get("Location", "")
        print(
            f"⛔ Redirect {r.status_code} to {loc} (likely not authorized)",
            file=sys.stderr,
        )
        return 5

    if r.status_code == 401:
        try:
            preview = (r.text or "")[:300].replace("\n", " ")
        except Exception:
            preview = ""
        print(f"⛔ 401 Unauthorized. Preview: {preview}", file=sys.stderr)
        return 1

    ctype = r.headers.get("Content-Type", "")
    if "application/json" not in ctype:
        print(
            f"⛔ Non-JSON ({ctype}). First 200 chars:\n{(r.text or '')[:200]}",
            file=sys.stderr,
        )
        return 5

    # Unknown non-200
    print(f"⛔ HTTP {r.status_code}: {(r.text or '')[:200]}", file=sys.stderr)
    return 5


if __name__ == "__main__":
    sys.exit(main())
