# src/fppull/qc_player_breakdown.py
import argparse
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

# Must match compute_points.py baseline weights
WEIGHTS = {
    "PPR": 1.0,
    "PASS_YD": 0.04,
    "PASS_TD": 4.0,
    "INT": -2.0,
    "RUSH_YD": 0.1,
    "RUSH_TD": 6.0,
    "REC": 1.0,
    "REC_YD": 0.1,
    "REC_TD": 6.0,
    "FUM_LOST": -2.0,
    "K_FGM": 3.0,
    "XP": 1.0,
}


def compute_points_row(r):
    # pull numeric fields with defaults
    pass_cmp = r.get("pass_cmp", 0) or 0
    pass_att = r.get("pass_att", 0) or 0
    pass_yds = r.get("pass_yds", 0) or 0
    pass_td = r.get("pass_td", 0) or 0
    pass_int = r.get("pass_int", 0) or 0
    rush_att = r.get("rush_att", 0) or 0
    rush_yds = r.get("rush_yds", 0) or 0
    rush_td = r.get("rush_td", 0) or 0
    rec_tgt = r.get("rec_tgt", 0) or 0
    rec_rec = r.get("rec_rec", 0) or 0
    rec_yds = r.get("rec_yds", 0) or 0
    rec_td = r.get("rec_td", 0) or 0
    fum_lost = r.get("fum_lost", 0) or 0
    k_fgm = r.get("k_fgm", 0) or 0
    k_fga = r.get("k_fga", 0) or 0
    xp_made = r.get("xp_made", 0) or 0
    xp_att = r.get("xp_att", 0) or 0

    pts_pass = (
        pass_yds * WEIGHTS["PASS_YD"]
        + pass_td * WEIGHTS["PASS_TD"]
        + pass_int * WEIGHTS["INT"]
    )
    pts_rush = rush_yds * WEIGHTS["RUSH_YD"] + rush_td * WEIGHTS["RUSH_TD"]
    pts_rec = (
        rec_rec * WEIGHTS["REC"]
        + rec_yds * WEIGHTS["REC_YD"]
        + rec_td * WEIGHTS["REC_TD"]
    )
    pts_kick = k_fgm * WEIGHTS["K_FGM"] + xp_made * WEIGHTS["XP"]
    pts_misc = fum_lost * WEIGHTS["FUM_LOST"]

    total = round(pts_pass + pts_rush + pts_rec + pts_kick + pts_misc, 2)

    breakdown = {
        "pass_cmp": pass_cmp,
        "pass_att": pass_att,
        "pass_yds": pass_yds,
        "pass_td": pass_td,
        "pass_int": pass_int,
        "rush_att": rush_att,
        "rush_yds": rush_yds,
        "rush_td": rush_td,
        "rec_tgt": rec_tgt,
        "rec_rec": rec_rec,
        "rec_yds": rec_yds,
        "rec_td": rec_td,
        "k_fgm": k_fgm,
        "k_fga": k_fga,
        "xp_made": xp_made,
        "xp_att": xp_att,
        "fum_lost": fum_lost,
        "pts_pass": round(pts_pass, 2),
        "pts_rush": round(pts_rush, 2),
        "pts_rec": round(pts_rec, 2),
        "pts_kick": round(pts_kick, 2),
        "pts_misc": round(pts_misc, 2),
        "pts_total": total,
    }
    return breakdown


def main():
    load_dotenv(ROOT / ".env")
    season = int(os.getenv("SEASON", "0"))
    if not season:
        raise SystemExit("Set SEASON in .env")

    parser = argparse.ArgumentParser(
        description="QC: per-player/week fantasy points breakdown from public wide stats."
    )
    parser.add_argument("--week", type=int, required=True, help="Week number (e.g., 1)")
    parser.add_argument(
        "--player", type=str, default="", help='Player name (e.g., "Kyler Murray")'
    )
    parser.add_argument("--athlete_id", type=str, default="", help="ESPN athlete id")
    parser.add_argument(
        "--team_abbr",
        type=str,
        default="",
        help="NFL team abbr to disambiguate (e.g., ARI)",
    )
    args = parser.parse_args()

    wide_path = PROC / f"season_{season}" / "player_week_stats_wide.csv"
    if not wide_path.exists():
        raise SystemExit(f"Wide stats not found: {wide_path}")

    df = pd.read_csv(wide_path)
    df = df[df["week"] == args.week].copy()

    if args.athlete_id:
        df = df[df["athlete_id"].astype(str) == str(args.athlete_id)]
    elif args.player:
        df = df[df["athlete_name"].str.contains(args.player, case=False, na=False)]
    else:
        raise SystemExit("Provide --player 'Name' or --athlete_id ID")

    if args.team_abbr:
        df = df[df["team_abbr"].str.upper() == args.team_abbr.upper()]

    if df.empty:
        raise SystemExit("No matching player rows for the given filters.")

    # If multiple matches, show them and exit
    if len(df) > 1:
        print("Multiple matches; refine with --team_abbr or use --athlete_id:")
        print(
            df[["team_abbr", "athlete_id", "athlete_name", "position"]].to_string(
                index=False
            )
        )
        return

    row = df.iloc[0].to_dict()
    breakdown = compute_points_row(row)

    header = {
        "season": int(row.get("season", 0)),
        "week": int(row.get("week", 0)),
        "team_abbr": row.get("team_abbr", ""),
        "athlete_id": row.get("athlete_id", ""),
        "athlete_name": row.get("athlete_name", ""),
        "position": row.get("position", ""),
    }

    print(
        "\n=== Player Week Breakdown (public wide stats → league compute weights) ==="
    )
    for k, v in header.items():
        print(f"{k:>12}: {v}")

    print("\n--- Raw stat line ---")
    stat_keys = [
        "pass_cmp",
        "pass_att",
        "pass_yds",
        "pass_td",
        "pass_int",
        "rush_att",
        "rush_yds",
        "rush_td",
        "rec_tgt",
        "rec_rec",
        "rec_yds",
        "rec_td",
        "k_fgm",
        "k_fga",
        "xp_made",
        "xp_att",
        "fum_lost",
    ]
    print({k: int(row.get(k, 0) or 0) for k in stat_keys})

    print("\n--- Points breakdown (current weights) ---")
    for k in ["pts_pass", "pts_rush", "pts_rec", "pts_kick", "pts_misc", "pts_total"]:
        print(f"{k:>10}: {breakdown[k]}")

    print("\nWeights used (must match compute_points.py):")
    for k, v in WEIGHTS.items():
        print(f"  {k:>10} = {v}")


if __name__ == "__main__":
    main()
