# src/fppull/join_public_private.py
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def _load_csv(path: Path, expected_cols: tuple[str, ...]) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing input file: {path}")
    df = pd.read_csv(path)
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise SystemExit(f"{path} missing required columns: {missing}")
    return df


def build_join(
    points_csv: Path,
    roster_csv: Path,
    teams_csv: Path | None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Returns (team_week_points, player_missing_points, report_dict).
    Inputs must contain at least:
      - points_csv: columns [season, week, athlete_id, official_pts]
      - roster_csv: columns [season, week, fantasy_team_id, athlete_id]
      - teams_csv (optional): [fantasy_team_id, team_name]
    """
    pts = _load_csv(points_csv, ("season", "week", "athlete_id", "official_pts"))
    # Be tolerant of ints/floats; normalize dtypes
    pts["season"] = pts["season"].astype(int)
    pts["week"] = pts["week"].astype(int)
    pts["athlete_id"] = pts["athlete_id"].astype(int)

    ros = _load_csv(roster_csv, ("season", "week", "fantasy_team_id", "athlete_id"))
    ros["season"] = ros["season"].astype(int)
    ros["week"] = ros["week"].astype(int)
    ros["athlete_id"] = ros["athlete_id"].astype(int)
    ros["fantasy_team_id"] = ros["fantasy_team_id"].astype(int)

    # Left-join roster → points (so we can detect missing points)
    merged = ros.merge(
        pts[["season", "week", "athlete_id", "official_pts"]],
        on=["season", "week", "athlete_id"],
        how="left",
        validate="many_to_one",
    )

    # Missing rows: rostered but no points
    missing = merged[merged["official_pts"].isna()].copy()
    missing = missing[["season", "week", "fantasy_team_id", "athlete_id"]].sort_values(
        ["season", "week", "fantasy_team_id", "athlete_id"]
    )

    # Replace NaN with 0.0 for aggregation
    merged["official_pts"] = merged["official_pts"].fillna(0.0)

    # Optional teams lookup
    if teams_csv and Path(teams_csv).exists():
        teams = _load_csv(Path(teams_csv), ("fantasy_team_id",))
        if "team_name" not in teams.columns:
            teams["team_name"] = teams["fantasy_team_id"].astype(str)
        teams["fantasy_team_id"] = teams["fantasy_team_id"].astype(int)
    else:
        teams = pd.DataFrame(columns=["fantasy_team_id", "team_name"])

    # Aggregate to team/week
    team_week = (
        merged.groupby(["season", "week", "fantasy_team_id"], as_index=False)[
            "official_pts"
        ]
        .sum()
        .rename(columns={"official_pts": "official_pts_total"})
        .sort_values(["season", "week", "fantasy_team_id"])
        .reset_index(drop=True)
    )

    # Attach team_name if available
    if not teams.empty:
        team_week = team_week.merge(
            teams[["fantasy_team_id", "team_name"]].drop_duplicates(),
            on="fantasy_team_id",
            how="left",
            validate="many_to_one",
        )

    # Report metrics
    expected_join_keys = ros[["season", "week", "athlete_id"]].drop_duplicates()
    got_join_keys = pts[["season", "week", "athlete_id"]].drop_duplicates()
    rows_ros = len(expected_join_keys)
    rows_pts = len(got_join_keys)
    rows_missing = len(missing)
    pct_coverage = 0.0 if rows_ros == 0 else (1.0 - rows_missing / rows_ros) * 100.0

    report = {
        "rows_roster_keys": rows_ros,
        "rows_points_keys": rows_pts,
        "missing_players": rows_missing,
        "pct_coverage": round(pct_coverage, 4),
    }

    return team_week, missing, report


def main() -> None:
    p = argparse.ArgumentParser(
        description="Join public player-week points to private league roster context."
    )
    p.add_argument(
        "--points", type=Path, default=Path("data/processed/player_week_points.csv")
    )
    p.add_argument(
        "--roster", type=Path, default=Path("data/processed/roster_week.csv")
    )
    p.add_argument("--teams", type=Path, default=Path("data/processed/teams.csv"))
    p.add_argument(
        "--out-team-week",
        type=Path,
        default=Path("data/processed/team_week_points.csv"),
    )
    p.add_argument(
        "--out-missing",
        type=Path,
        default=Path("data/processed/player_missing_points.csv"),
    )
    p.add_argument(
        "--out-report",
        type=Path,
        default=Path("data/processed/join_report.json"),
    )
    args = p.parse_args()

    args.out_team_week.parent.mkdir(parents=True, exist_ok=True)
    args.out_missing.parent.mkdir(parents=True, exist_ok=True)
    args.out_report.parent.mkdir(parents=True, exist_ok=True)

    tw, miss, rep = build_join(args.points, args.roster, args.teams)

    tw.to_csv(args.out_team_week, index=False)
    miss.to_csv(args.out_missing, index=False)
    args.out_report.write_text(json.dumps(rep, indent=2))
    print(
        f"✅ wrote {args.out_team_week} ({len(tw)} rows)\n"
        f"✅ wrote {args.out_missing} ({len(miss)} rows)\n"
        f"✅ wrote {args.out_report}\n"
        f"coverage={rep['pct_coverage']}% missing={rep['missing_players']}"
    )


if __name__ == "__main__":
    main()
