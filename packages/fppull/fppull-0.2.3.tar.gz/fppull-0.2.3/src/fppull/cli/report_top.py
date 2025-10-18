from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> int:
    p = argparse.ArgumentParser(description="Show top scorers from joined season data")
    p.add_argument(
        "--in",
        dest="inp",
        required=True,
        help="Path to season_YYYY_joined.csv (from pull_range)",
    )
    p.add_argument("--top", type=int, default=20, help="How many rows to show")
    p.add_argument(
        "--group-by",
        choices=["player", "position", "team"],
        default="player",
        help="Aggregate totals by player (default), position, or team",
    )
    p.add_argument(
        "--min-weeks",
        type=int,
        default=0,
        help="Minimum distinct weeks required to include a row (0 = no filter)",
    )
    p.add_argument(
        "--ppg",
        action="store_true",
        help="Include points_per_game when week column exists",
    )
    p.add_argument(
        "--format",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format: pretty table (default), CSV, or JSON",
    )
    p.add_argument(
        "--out",
        type=str,
        default="",
        help="Optional path to write output; uses --format to choose file type",
    )
    args = p.parse_args()

    inp = Path(args.inp)
    df = pd.read_csv(inp)

    # Basic requirements
    if "points" not in df.columns:
        raise SystemExit("Input is missing required column: 'points'")

    # Grouping keys + validation per mode
    if args.group_by == "player":
        need = {"player_id"}
        keys = ["player_id"]
    elif args.group_by == "position":
        need = {"position"}
        keys = ["position"]
    else:  # team
        need = {"team_name"}
        keys = ["team_name"]

    missing = need - set(df.columns)
    if missing:
        raise SystemExit(
            f"Input missing required columns for --group-by={args.group_by}: {missing}"
        )

    # Build aggregation spec
    agg = {"points_total": ("points", "sum")}
    have_week = "week" in df.columns
    if have_week:
        agg["weeks_played"] = ("week", "nunique")
    elif args.min_weeks > 0:
        raise SystemExit("--min-weeks requires a 'week' column in input")

    grp = (
        df.groupby(keys, dropna=False, as_index=False)
        .agg(**agg)
        .sort_values("points_total", ascending=False)
    )

    # Join back readable metadata for player mode (first occurrence)
    if args.group_by == "player":
        meta_cols = [c for c in ["team_name", "position"] if c in df.columns]
        if meta_cols:
            first_meta = df.drop_duplicates(subset=["player_id"])[
                ["player_id"] + meta_cols
            ]
            grp = grp.merge(first_meta, on="player_id", how="left")

    # Apply min-weeks filter if requested
    if args.min_weeks > 0 and have_week:
        grp = grp[grp["weeks_played"] >= int(args.min_weeks)]

    # Optionally add points_per_game
    if args.ppg and have_week:
        # avoid divide-by-zero; weeks_played is nunique so zero is unlikely, but be safe
        grp["points_per_game"] = grp["points_total"] / grp["weeks_played"].replace(
            {0: pd.NA}
        )

    # Reorder columns nicely
    if args.group_by == "player":
        cols = ["player_id", "points_total"]
        if have_week:
            cols.append("weeks_played")
        if args.ppg and have_week:
            cols.append("points_per_game")
        for c in ["team_name", "position"]:
            if c in grp.columns:
                cols.append(c)
        grp = grp[cols]
    else:
        cols = keys + ["points_total"]
        if have_week:
            cols.append("weeks_played")
        if args.ppg and have_week:
            cols.append("points_per_game")
        grp = grp[cols]

    # Limit rows
    grp = grp.head(args.top)

    # If --out is provided, write to file using chosen format
    if args.out:
        outp = Path(args.out)
        outp.parent.mkdir(parents=True, exist_ok=True)
        if args.format == "json":
            outp.write_text(grp.to_json(orient="records"))
        elif args.format == "csv":
            grp.to_csv(outp, index=False)
        else:
            # table -> write a pretty text table
            outp.write_text(grp.to_string(index=False))
        return 0

    # Otherwise print to stdout in the chosen format
    if args.format == "json":
        print(grp.to_json(orient="records"))
    elif args.format == "csv":
        print(grp.to_csv(index=False), end="")
    else:
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(grp.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
