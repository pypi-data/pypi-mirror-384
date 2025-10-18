# src/fppull/private_league.py
# import argparse
# import contextlib
# import os
# from pathlib import Path
# import pandas as pd
# from dotenv import load_dotenv
# # Reuse existing ESPN helpers from your codebase
# from fppull.fetch_espn_team_scores import (
#     _get_json,
# )  # noqa: F401  (auth used implicitly by _get_json)
# src/fppull/private_league.py (top of file)
import argparse
import contextlib
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from fppull.fetch_espn_team_scores import _get_json  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

# --- add near the top ---
LINEUP_SLOT_NAME = {
    0: "QB",
    2: "RB",
    4: "WR",
    6: "TE",
    16: "DST",
    17: "IDP",
    20: "BN",
    21: "IR",
    23: "FLEX",
    24: "WRRB",
    25: "WRTE",
    26: "RBTE",
    27: "QBRBWRTE",
    78: "OP",
    5: "RB/WR",
    7: "TE/WR",
    3: "RB/WR/TE",
    12: "DP",
    19: "HC",
}


def _slot_name(slot_id: int) -> str:
    return LINEUP_SLOT_NAME.get(slot_id, str(slot_id))


def fetch_rosters_df(season: int, league_id: str, weeks: list[int]) -> pd.DataFrame:
    """
    Pull weekly rosters (mRoster) → one row per player on a fantasy roster that week.
    Columns: season, week, team_id, athlete_id, athlete_name, lineup_slot, status
    """
    base = _base_url(season, league_id)
    rows: list[dict] = []

    for wk in weeks:
        data = _get_json(base, params={"view": "mRoster", "scoringPeriodId": wk})
        for t in data.get("teams") or []:
            team_id = t.get("id")
            roster = (t.get("roster") or {}).get("entries") or []
            for e in roster:
                player = (e.get("playerPoolEntry") or {}).get("player") or {}
                athlete_id = player.get("id")
                athlete_name = player.get("fullName") or player.get("name") or ""
                slot_id = e.get("lineupSlotId")
                status = (
                    "starter" if slot_id not in (20, 21) else "bench"
                )  # BN/IR -> bench
                rows.append(
                    dict(
                        season=season,
                        week=wk,
                        team_id=team_id,
                        athlete_id=athlete_id,
                        athlete_name=athlete_name,
                        lineup_slot=(
                            _slot_name(int(slot_id)) if slot_id is not None else ""
                        ),
                        status=status,
                    )
                )

    # Build the roster dataframe (no matchup fields here)
    df = (
        pd.DataFrame(rows)
        .sort_values(["week", "team_id", "lineup_slot", "athlete_name"])
        .reset_index(drop=True)
    )
    return df

    # --- BEGIN: synthesize matchup_id if ESPN omits it (charter: fail-safe, deterministic) ---
    # Create a stable pair key per row (order-independent)
    pair = df.apply(
        lambda r: tuple(sorted((int(r["team_id"]), int(r["opponent_team_id"])))),
        axis=1,
    )
    df = df.assign(_pair=pair)

    # If matchup_id column is missing or all blank, build 1..N ids per week
    if "matchup_id" not in df.columns or df["matchup_id"].isna().all():
        df["matchup_id"] = df.groupby("week")["_pair"].transform(
            lambda s: pd.factorize(s)[0] + 1
        )
    else:
        # Only fill blanks, leave existing non-null ids untouched
        need = df["matchup_id"].isna()
        if need.any():
            df.loc[need, "matchup_id"] = (
                df.loc[need]
                .groupby("week")["_pair"]
                .transform(lambda s: pd.factorize(s)[0] + 1)
            )

    # Cleanup + type
    df = df.drop(columns=["_pair"])
    df["matchup_id"] = df["matchup_id"].astype(int)
    # --- END: synthesize matchup_id ---


def write_rosters_csv(season: int, df: pd.DataFrame) -> str:
    out_dir = ROOT / "data" / "processed" / f"season_{season}" / "private"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "roster_week.csv"
    df.to_csv(out_path, index=False)
    return str(out_path)


def _base_url(season: int, league_id: str) -> str:
    return f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"


def fetch_teams_df(season: int, league_id: str) -> pd.DataFrame:
    """
    Pull teams and map owner GUID -> display name when possible.
    """
    base = _base_url(season, league_id)

    # First call: mTeam (teams + often members)
    data = _get_json(base, params={"view": "mTeam"})

    # Build a member-id -> displayName map (best effort)
    member_name = {}
    for m in data.get("members") or []:
        mid = m.get("id")
        dname = m.get("displayName") or m.get("firstName") or m.get("nickname")
        if mid and dname:
            member_name[str(mid)] = str(dname)

    # If members weren’t present, try mSettings (some leagues put members there)
    if not member_name:
        try:
            sdata = _get_json(base, params={"view": "mSettings"})
            for m in sdata.get("members") or []:
                mid = m.get("id")
                dname = m.get("displayName") or m.get("firstName") or m.get("nickname")
                if mid and dname:
                    member_name[str(mid)] = str(dname)
        except Exception:
            pass  # still fine; we’ll leave GUIDs if we can’t resolve names

    rows = []
    for t in data.get("teams", []):
        team_id = t.get("id")
        abbr = t.get("abbrev")

        # Prefer single 'name'; else fallback to location + nickname; else abbrev
        name = (t.get("name") or "").strip()
        if not name:
            loc = (t.get("location") or "").strip()
            nick = (t.get("nickname") or "").strip()
            combo = (loc + " " + nick).strip()
            name = combo or (abbr or f"Team {team_id}")

        # Owner resolution
        owner_raw = None
        owners = t.get("owners") or []
        if owners:
            owner_raw = str(owners[0])
        owner = member_name.get(owner_raw, owner_raw)

        rows.append(
            {
                "season": season,
                "team_id": team_id,
                "team_abbr": abbr,
                "team_name": name,
                "owner": owner,
            }
        )

    return pd.DataFrame(rows).sort_values(["team_id"]).reset_index(drop=True)


# --- matchups (mMatchup) ---
def _is_for_week_sched(obj: dict, wk: int) -> bool:
    """
    True if this schedule object corresponds to the requested fantasy week.
    Priority:
      1) matchupPeriodId == wk
      2) pointsByScoringPeriod has wk
      3) scoringPeriodId fields match wk (rare)
    """
    try:
        mp = obj.get("matchupPeriodId")
        if isinstance(mp, int) and mp == wk:
            return True
        # Newer shapes sometimes tuck scoring by week in these dicts
        home = obj.get("home") or {}
        away = obj.get("away") or {}
        for side in (home, away):
            psp = side.get("pointsByScoringPeriod") or {}
            # keys can be str
            if str(wk) in {str(k) for k in psp}:
                return True
        # Last resort: explicit scoringPeriodId on the object (uncommon)
        spi = obj.get("scoringPeriodId")
        if isinstance(spi, int) and spi == wk:
            return True
    except Exception:
        pass
    return False


def fetch_matchups_df(season: int, league_id: str, weeks: list[int]) -> pd.DataFrame:
    """
    One row per team per matchup per week.
    Columns: season, week, matchup_id, team_id, opponent_team_id, home_away
    """
    base = _base_url(season, league_id)
    rows: list[dict] = []

    for wk in weeks:
        data = _get_json(
            base, params={"view": "mMatchup"}
        )  # don’t rely on scoringPeriodId filter
        sched = data.get("schedule") or []
        # keep only items for this wk
        sched = [m for m in sched if _is_for_week_sched(m, wk)]

        for m in sched:
            matchup_id = m.get("matchupId")
            teams = m.get("teams")

            if teams:  # legacy array
                if len(teams) == 2:
                    a, b = teams[0], teams[1]
                    rows += [
                        dict(
                            season=season,
                            week=wk,
                            matchup_id=matchup_id,
                            team_id=a.get("teamId"),
                            opponent_team_id=b.get("teamId"),
                            home_away=a.get("homeAway", ""),
                        ),
                        dict(
                            season=season,
                            week=wk,
                            matchup_id=matchup_id,
                            team_id=b.get("teamId"),
                            opponent_team_id=a.get("teamId"),
                            home_away=b.get("homeAway", ""),
                        ),
                    ]
            else:  # newer home/away
                home = m.get("home") or {}
                away = m.get("away") or {}
                if home.get("teamId") and away.get("teamId"):
                    rows += [
                        dict(
                            season=season,
                            week=wk,
                            matchup_id=matchup_id,
                            team_id=home["teamId"],
                            opponent_team_id=away["teamId"],
                            home_away="home",
                        ),
                        dict(
                            season=season,
                            week=wk,
                            matchup_id=matchup_id,
                            team_id=away["teamId"],
                            opponent_team_id=home["teamId"],
                            home_away="away",
                        ),
                    ]

    df = pd.DataFrame(rows).dropna(subset=["team_id", "opponent_team_id"])

    # --- BEGIN: synthesize matchup_id if ESPN omits it ---
    # Create a stable pair key per row (order-independent)
    pair = df.apply(
        lambda r: tuple(sorted((int(r["team_id"]), int(r["opponent_team_id"])))),
        axis=1,
    )
    df = df.assign(_pair=pair)

    # If matchup_id column is missing or all blank, build 1..N ids per week
    if "matchup_id" not in df.columns or df["matchup_id"].isna().all():
        df["matchup_id"] = df.groupby("week")["_pair"].transform(
            lambda s: pd.factorize(s)[0] + 1
        )
    else:
        # Only fill blanks, leave existing non-null ids untouched
        need = df["matchup_id"].isna()
        if need.any():
            df.loc[need, "matchup_id"] = (
                df.loc[need]
                .groupby("week")["_pair"]
                .transform(lambda s: pd.factorize(s)[0] + 1)
            )

    df = df.drop(columns=["_pair"])
    df["matchup_id"] = df["matchup_id"].astype(int)
    # --- END: synthesize matchup_id ---

    # ensure ints and order
    for c in ("team_id", "opponent_team_id", "week"):
        df[c] = df[c].astype(int)
    df = df.sort_values(["week", "matchup_id", "team_id"]).reset_index(drop=True)
    return df


def write_matchups_csv(season: int, df: pd.DataFrame) -> str:
    out_dir = ROOT / "data" / "processed" / f"season_{season}" / "private"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "matchups.csv"
    df.to_csv(out_path, index=False)
    return str(out_path)


def main() -> None:
    load_dotenv()  # pick up SEASON, LEAGUE_ID, COOKIE_FILE, etc.
    p = argparse.ArgumentParser(
        description="Fetch private ESPN league context (teams)."
    )
    p.add_argument("--season", type=int, default=int(os.getenv("SEASON", "2025")))
    p.add_argument(
        "--league-id",
        type=str,
        default=os.getenv("LEAGUE_ID", "").strip(),
        required=False,
    )
    args = p.parse_args()

    season = args.season
    league_id = args.league_id or os.getenv("LEAGUE_ID", "").strip()
    if not league_id:
        raise SystemExit("LEAGUE_ID is required (set in .env or pass --league-id).")

    out_dir = PROCESSED / f"season_{season}" / "private"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Fetch and write teams.csv
    print(
        f"[private_league] fetching teams for season={season}, league_id={league_id} …"
    )
    teams_df = fetch_teams_df(season, league_id)
    out_csv = out_dir / "teams.csv"
    teams_df.to_csv(out_csv, index=False)
    print(f"✅ wrote {out_csv} ({len(teams_df)} rows)")
    if not teams_df.empty:
        print(teams_df.head().to_string(index=False))

    # --- roster slice ---
    weeks_arg = os.getenv("WEEKS", "").strip()
    if weeks_arg and weeks_arg.upper() != "ALL":
        weeks = [int(w) for w in weeks_arg.split(",") if w.strip()]
    else:
        weeks = list(
            range(1, 15)
        )  # adjust if your league’s regular season spans more/less

    print(f"[private_league] fetching rosters for weeks={weeks} …")
    rdf = fetch_rosters_df(season=season, league_id=league_id, weeks=weeks)
    out = write_rosters_csv(season, rdf)
    print(f"✅ wrote {out} ({len(rdf)} rows)")
    with contextlib.suppress(Exception):
        # Tiny preview
        print(rdf.head(10).to_string(index=False))

    # --- matchups slice ---
    print(f"[private_league] fetching matchups for weeks={weeks} …")
    mdf = fetch_matchups_df(season=season, league_id=league_id, weeks=weeks)
    mout = write_matchups_csv(season, mdf)
    print(f"✅ wrote {mout} ({len(mdf)} rows)")
    with contextlib.suppress(Exception):
        print(mdf.head(10).to_string(index=False))


if __name__ == "__main__":
    main()


def fetch_roster_df(season: int, league_id: str | None = None):
    """Offline-safe roster source for reports/tests.

    Looks for data/samples/roster_{season}.csv with columns:
    team_id, team_name, player_id, position
    Falls back to a tiny in-memory default if the file is missing.
    """
    from pathlib import Path

    import pandas as pd

    sample = Path(f"data/samples/roster_{season}.csv")
    if sample.exists():
        return pd.read_csv(sample)

    # Fallback: small default so joins/tests don't break
    return pd.DataFrame(
        {
            "team_id": [10, 11, 12],
            "team_name": ["A", "B", "C"],
            "player_id": [1, 2, 999],
            "position": ["WR", "RB", "QB"],
        }
    )
