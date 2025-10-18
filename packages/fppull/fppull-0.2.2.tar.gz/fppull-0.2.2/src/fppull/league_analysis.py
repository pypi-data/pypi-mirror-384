# src/fppull/league_analysis.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="League Analysis: summarize team points per season and (optionally) export Excel."
    )
    p.add_argument(
        "--team-week",
        default="data/processed/team_week_points.csv",
        help="Input CSV with columns [season, week, fantasy_team_id, official_pts_total, team_name?].",
    )
    p.add_argument(
        "--out-summary",
        default="data/processed/league_summary.csv",
        help="Output CSV summary (per season, team totals + rank).",
    )
    p.add_argument(
        "--out-excel",
        default="data/processed/League_Analysis.xlsx",
        help="Optional Excel workbook (two sheets) — skipped if openpyxl unavailable.",
    )
    p.add_argument(
        "--season",
        type=int,
        default=None,
        help="If set, filter to a single season before summarizing.",
    )
    return p


def load_team_week(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing input file: {path}")
    df = pd.read_csv(path)
    required = {"season", "week", "fantasy_team_id", "official_pts_total"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"{path} missing columns: {sorted(missing)}")
    # Optional: team_name
    if "team_name" not in df.columns:
        df["team_name"] = df["fantasy_team_id"].astype(str)
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    # Per season × team totals
    agg = (
        df.groupby(["season", "fantasy_team_id", "team_name"], dropna=False)[
            "official_pts_total"
        ]
        .sum()
        .reset_index()
        .rename(columns={"official_pts_total": "season_pts_total"})
    )
    # Rank within season (1 = best)
    agg["season_rank"] = (
        agg.groupby("season")["season_pts_total"]
        .rank(method="min", ascending=False)
        .astype(int)
    )
    # Nice order
    agg = agg.sort_values(["season", "season_rank", "fantasy_team_id"]).reset_index(
        drop=True
    )
    return agg


def weekly_pivot(df: pd.DataFrame) -> pd.DataFrame:
    # pivot: rows = team_name (or id), cols = week, values = official_pts_total
    pv = (
        df.pivot_table(
            index=["season", "fantasy_team_id", "team_name"],
            columns="week",
            values="official_pts_total",
            aggfunc="sum",
            fill_value=0.0,
        )
        .sort_index()
        .reset_index()
    )
    # make week columns tidy: w1, w2, ...
    pv.columns = [
        (f"w{c}" if isinstance(c, int | float) else c)
        for c in pv.columns  # weeks become wN
    ]
    return pv


def maybe_write_excel(
    out_path: Path, team_summary: pd.DataFrame, weekly: pd.DataFrame
) -> None:
    try:
        import openpyxl  # noqa: F401  (import only to check availability)
    except Exception:
        # Keep CLI happy in CI if openpyxl not preinstalled
        print("openpyxl not available — skipping Excel export", file=sys.stderr)
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as xls:
        team_summary.to_excel(xls, sheet_name="team_season_summary", index=False)
        weekly.to_excel(xls, sheet_name="weekly_team_points", index=False)
    print(f"✅ wrote {out_path}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    team_week_path = Path(args.team_week)
    out_summary_path = Path(args.out_summary)
    out_excel_path = Path(args.out_excel)

    df = load_team_week(team_week_path)
    if args.season is not None:
        df = df[df["season"] == args.season].copy()

    summary = summarize(df)
    weekly = weekly_pivot(df)

    out_summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_summary_path, index=False)
    print(f"✅ wrote {out_summary_path} ({len(summary)} rows)")

    maybe_write_excel(out_excel_path, summary, weekly)

    # tiny console report
    for season, chunk in summary.groupby("season"):
        top = chunk.nsmallest(3, "season_rank")
        leaders = ", ".join(
            f"{row.team_name}({row.season_pts_total:.1f})" for _, row in top.iterrows()
        )
        print(f"season {season}: leaders → {leaders}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
