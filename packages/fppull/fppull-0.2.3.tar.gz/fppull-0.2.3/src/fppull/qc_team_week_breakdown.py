# src/fppull/qc_team_week_breakdown.py
import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"


def main():
    load_dotenv(ROOT / ".env")
    season = int(os.getenv("SEASON", "0"))
    if not season:
        raise SystemExit("Set SEASON in .env")

    parser = argparse.ArgumentParser(
        description="QC: list team starters & points for a given week and compare to ESPN official total."
    )
    parser.add_argument("--week", type=int, required=True)
    parser.add_argument(
        "--team", type=str, required=True, help='Fantasy team name (e.g., "LAMBO")'
    )
    args = parser.parse_args()

    base = PROC / f"season_{season}"
    points_path = base / "league_player_points.csv"
    official_path = base / "espn" / "team_week_official.csv"

    if not points_path.exists():
        raise SystemExit(
            f"Computed league player points not found: {points_path}. Run join_league_points.py"
        )
    pts = pd.read_csv(points_path)

    # filter week + team
    sub = pts[
        (pts["week"] == args.week)
        & (pts["fantasy_team_name"].str.lower() == args.team.lower())
    ].copy()
    if sub.empty:
        # Try contains (some leagues have emojis or trailing spaces)
        sub = pts[
            (pts["week"] == args.week)
            & (pts["fantasy_team_name"].str.contains(args.team, case=False, na=False))
        ].copy()

    if sub.empty:
        raise SystemExit(
            f"No rows found for week {args.week} and team '{args.team}'. "
            "Use `python - << 'PY'` to inspect unique team names if needed."
        )

    # show lineup_slot distribution so we can verify what's being treated as starters
    print("\n=== Lineup slot distribution (raw) ===")
    print(sub["lineup_slot"].value_counts(dropna=False).to_string())
    # Heuristic for starters:
    # - lineup_slot is a number (not NaN)
    # - and < 20 (ESPN typically uses low integers for starters, 20+ for benches/IR).
    # If this is wrong for your league, we can refine the mapping.
    starters = sub[
        (~sub["lineup_slot"].isna())
        & (pd.to_numeric(sub["lineup_slot"], errors="coerce") < 20)
    ].copy()

    print("\n=== Starters detected by heuristic (lineup_slot < 20) ===")
    if starters.empty:
        print(
            "No starters detected by heuristic. We need to adjust lineup_slot mapping."
        )
    cols = [
        "athlete_name",
        "position",
        "lineup_slot",
        "pts_ppr",
        "pts_pass",
        "pts_rush",
        "pts_rec",
        "pts_kick",
        "pts_misc",
    ]
    print(starters[cols].sort_values("lineup_slot").to_string(index=False))

    computed_sum = round(starters["pts_ppr"].sum(), 2)
    print(f"\nComputed starters PPR sum: {computed_sum:.2f}")

    # Try to load official and compare
    official = None
    if official_path.exists():
        off = pd.read_csv(official_path)
        off_sub = off[(off["season"] == season) & (off["week"] == args.week)]
        # Try exact match on team name, else contains
        off_sub_exact = off_sub[
            off_sub["fantasy_team_name"].str.lower() == args.team.lower()
        ]
        off_sub_contains = off_sub[
            off_sub["fantasy_team_name"].str.contains(args.team, case=False, na=False)
        ]
        if len(off_sub_exact) == 1:
            official = float(off_sub_exact.iloc[0]["official_pts"])
        elif len(off_sub_contains) == 1:
            official = float(off_sub_contains.iloc[0]["official_pts"])

    if official is None:
        print(
            "\n(No official total found for that team+week in team_week_official.csv)"
        )
    else:
        delta = round(computed_sum - official, 2)
        print(f"Official ESPN team total: {official:.2f}")
        print(f"Delta (computed - official): {delta:.2f}")

    # Show a quick sanity count of starters vs all rows for context
    print(f"\nRows for team/week: {len(sub)}  |  Starters counted: {len(starters)}")


if __name__ == "__main__":
    main()
