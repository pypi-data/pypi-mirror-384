# src/fppull/fetch_espn_scoring.py
# json already imported at top
import os
import sys
from pathlib import Path
from typing import Any
import json as _json

import pandas as pd
import requests
from dotenv import load_dotenv
from urllib.parse import unquote as _url_unquote


ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = ROOT / "data" / "processed"
RAW_BASE = ROOT / "data" / "raw"

READS_BASE_TMPL = (
    "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/"
    "seasons/{season}/segments/0/leagues/{league_id}"
)

# Optional convenience names for common statIds.
# This is NOT exhaustive and is only for readability in the CSV if ids match.
WELL_KNOWN = {
    # Passing
    3: "PASS_YDS",  # historically pass yards per yard -> 0.04 in many leagues
    25: "PASS_TD",
    26: "PASS_INT",
    29: "PASS_2PT",  # two-pt pass
    # Rushing
    24: "RUSH_YDS",
    27: "RUSH_TD",
    32: "RUSH_2PT",
    # Receiving
    42: "REC",  # per reception (PPR)
    43: "REC_YDS",
    44: "REC_TD",
    45: "REC_2PT",
    # Fumbles
    52: "FUM_LOST",
    # Kicking (varies by league; ids are examples seen historically)
    74: "FG_MADE_0_39",
    77: "FG_MADE_40_49",
    80: "FG_MADE_50_59",
    83: "FG_MADE_60_PLUS",
    86: "XP_MADE",
    88: "FG_MISSED_TOTAL",
}


def _league_api_base() -> str:
    season = os.getenv("SEASON", "").strip()
    league_id = os.getenv("LEAGUE_ID", "").strip()
    if not season or not league_id:
        raise SystemExit("Set SEASON and LEAGUE_ID in .env")
    return READS_BASE_TMPL.format(season=season, league_id=league_id)


def _cookie_from_file(path: str) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    try:
        txt = p.read_text(encoding="utf-8").strip()
        return txt if ("SWID=" in txt or "espn_s2=" in txt) else None
    except Exception:
        return None


# --- add this helper above _get_json (or replace your current header-crafter) ---
def _cookie_header_from_env() -> str:
    """
    Build the Cookie header exactly like the working browser request:
      - SWID must be quoted and include braces
      - espn_s2 must be sent *as-is* (percent-encoded if that's what you copied)
    """
    swid_raw = os.getenv("SWID", "").strip()
    s2_raw = os.getenv("ESPN_S2", "").strip() or os.getenv("espn_s2", "").strip()
    if not swid_raw or not s2_raw:
        raise SystemExit(
            "Missing SWID or ESPN_S2. Run: python -m fppull.cli.env doctor"
        )

    # Ensure braces and quotes on SWID
    swid = swid_raw if swid_raw.startswith("{") else "{" + swid_raw.strip("{}") + "}"
    return f'SWID="{swid}"; espn_s2={s2_raw}'


def _auth_headers() -> dict[str, str]:
    cookie_header = None
    cookie_file = os.getenv("COOKIE_FILE", "").strip()
    if cookie_file:
        cookie_header = _cookie_from_file(cookie_file)

    if not cookie_header:
        swid = os.getenv("SWID", "").strip()
        s2_raw = os.getenv("ESPN_S2", "").strip()

        # Decode percent-encoded espn_s2 if needed (robust to both forms)
        s2 = _url_unquote(s2_raw) if s2_raw else ""

        parts = []
        if swid:
            # ESPN prefers SWID quoted, braces included
            swid_quoted = swid if swid.startswith("{") else "{" + swid.strip("{}") + "}"
            parts.append(f'SWID="{swid_quoted}"')
        if s2:
            # Send both casings to match browser behavior seen in the wild
            parts.append(f"espn_s2={s2}")
            parts.append(f"ESPN_S2={s2}")

        cookie_header = "; ".join(parts) if parts else None

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/127.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={os.getenv('LEAGUE_ID','')}",
        # These two are sometimes helpful but not strictly required; harmless to include:
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Platform": "kona-PROD",
    }
    if cookie_header:
        headers["Cookie"] = cookie_header

    # Optional debug echo
    if os.getenv("FPPULL_DEBUG"):
        preview = headers.get("Cookie", "")
        if preview:
            # mask most of the s2 for safety
            masked = preview.replace(s2, (s2[:6] + "…****" if len(s2) > 10 else "****"))
            print(f"→ Cookie: {masked}")
    return headers


def _get_json(url, params=None, headers=None, retries=3, x_filter=None):
    import time

    h = dict(headers or {})
    if x_filter:
        h["X-Fantasy-Filter"] = x_filter
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, headers=h, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            print(
                f"[WARN] HTTP {getattr(e.response,'status_code', '?')} on attempt {attempt}/{retries}"
            )
            if attempt == retries:
                raise
            time.sleep(2)
        except requests.RequestException as e:
            print(f"[WARN] Network error {e} (attempt {attempt}/{retries})")
            if attempt == retries:
                raise
            time.sleep(2)


def _flatten_scoring_items(settings: dict[str, Any]) -> pd.DataFrame:
    """
    ESPN embeds scoring under a few shapes. We’ll try the common ones:
      settings.scoringSettings.scoringItems -> list of {statId, points, ...}
    Fallbacks are kept generic; we emit whatever ESPN provides so you can audit.
    """
    items: list[dict[str, Any]] = []

    # Primary path: settings.scoringSettings.scoringItems
    path1 = (settings or {}).get("scoringSettings", {})
    if isinstance(path1, dict):
        raw_items = path1.get("scoringItems", [])
        if isinstance(raw_items, list) and raw_items:
            for it in raw_items:
                if not isinstance(it, dict):
                    continue
                row = dict(
                    statId=it.get("statId"),
                    points=it.get("points"),
                    isMulti=it.get("isMulti"),
                    # Keep extra metadata if present
                    **{
                        k: v
                        for k, v in it.items()
                        if k not in {"statId", "points", "isMulti"}
                    },
                )
                items.append(row)

    # If nothing found, try a couple of fallbacks that show up in older payloads
    if not items:
        # Sometimes modifiers live under 'statCategoryPoints' or similar custom keys
        for key in ("statCategoryPoints", "statModifiers", "scoringItems"):
            raw = (settings or {}).get(key, [])
            if isinstance(raw, list) and raw:
                for it in raw:
                    if isinstance(it, dict) and "statId" in it:
                        row = dict(
                            statId=it.get("statId"),
                            points=it.get("points", it.get("value")),
                            **{
                                k: v
                                for k, v in it.items()
                                if k not in {"statId", "points", "value"}
                            },
                        )
                        items.append(row)

    df = pd.DataFrame(items) if items else pd.DataFrame(columns=["statId", "points"])
    # Attach a friendly name when we recognize the statId
    if "statId" in df.columns:
        df["statName_guess"] = df["statId"].map(WELL_KNOWN).fillna("")
    return df


def main():
    load_dotenv(ROOT / ".env")

    season = os.getenv("SEASON")
    league_id = os.getenv("LEAGUE_ID")
    if not season or not league_id:
        print(
            "Config error: ensure SEASON and LEAGUE_ID are set in .env", file=sys.stderr
        )
        sys.exit(1)

    base = _league_api_base()
    out_dir = OUT_BASE / f"season_{season}" / "espn"
    raw_dir = RAW_BASE / f"season_{season}" / "espn"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Multiple views like the working cURL
    params = [
        ("view", "modular"),
        ("view", "mNav"),
        ("view", "mMatchupScore"),
        ("view", "mScoreboard"),
        ("view", "mStatus"),
        ("view", "mSettings"),
        ("view", "mTeam"),
        ("view", "mPendingTransactions"),
    ]
    # Optional filter via env, e.g.:
    #   export FPPULL_FILTER_JSON='{"schedule":{"filterCurrentMatchupPeriod":{"value":true}}}'
    x_filter = None
    if os.getenv("FPPULL_FILTER_JSON"):
        try:
            x_filter = _json.loads(os.getenv("FPPULL_FILTER_JSON"))
        except _json.JSONDecodeError:
            print("⚠️  FPPULL_FILTER_JSON is not valid JSON; ignoring.", file=sys.stderr)

    # json already imported at top

    cookie_header = _cookie_header_from_env()
    headers = {
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15; rv:143.0) "
            "Gecko/20100101 Firefox/143.0"
        ),
        "Origin": "https://fantasy.espn.com",
        "Referer": f"https://fantasy.espn.com/football/league?leagueId={os.getenv('LEAGUE_ID','')}",
        "X-Fantasy-Source": "kona",
        "X-Fantasy-Platform": "kona-PROD",
        "Cookie": cookie_header,
    }

    # If you built x_filter as a dict earlier, stringify it for the header:
    xf = _json.dumps(x_filter, separators=(",", ":")) if x_filter else None

    data = _get_json(base, params=params, headers=headers, x_filter=xf)

    # Save raw for audit
    (raw_dir / "msettings.json").write_text(_json.dumps(data, indent=2))

    # Normalize where "settings" lives
    settings = data.get("settings", data) if isinstance(data, dict) else {}
    df = _flatten_scoring_items(settings)

    # Emit files
    json_path = out_dir / "scoring_settings.json"
    csv_path = out_dir / "scoring_table.csv"
    json_path.write_text(_json.dumps(settings, indent=2))
    df.to_csv(csv_path, index=False)

    # Small summary for the console
    print(f"✅ Wrote {json_path}")
    print(f"✅ Wrote {csv_path} with {len(df)} rows.")
    if len(df) == 0:
        print("⚠️  No scoring items found. Inspect raw:", raw_dir / "msettings.json")
    else:
        sample = df.head(20).to_string(index=False)
        print("\nSample scoring rows:\n", sample)


if __name__ == "__main__":
    main()
