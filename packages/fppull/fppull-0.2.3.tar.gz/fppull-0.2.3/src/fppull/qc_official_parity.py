# src/fppull/qc_official_parity.py
"""
Compare our computed starter totals vs ESPN official team totals for each week.

It:
- Loads our totals: data/processed/season_{SEASON}/league_team_week_totals.csv
- Sniffs ESPN sources under .../espn/ to find official team points
  (supports: scoreboard.csv, matchups.csv, teams.csv with weekly points, etc.)
- Standardizes columns and builds (season, week, fantasy_team_id, official_pts)
- Joins and prints a parity report with helpful hints

Usage:
  python src/fppull/qc_official_parity.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
PROC_TPL = ROOT / "data" / "processed" / "season_{season}"
ESPN_DIR_TPL = PROC_TPL / "espn"

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 40)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def _load_env_season() -> str:
    load_dotenv(ROOT / ".env")
    s = os.getenv("SEASON", "").strip()
    if not s:
        print("Set SEASON in .env", file=sys.stderr)
        sys.exit(1)
    return s


def _read_csv(path: Path) -> pd.DataFrame | None:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception as e:
        print(f"⚠️  Failed reading {path}: {e}", file=sys.stderr)
    return None


def _as_float(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _as_int(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)


def _norm_team_id(s: pd.Series) -> pd.Series:
    return _as_int(s)


def _norm_week(s: pd.Series) -> pd.Series:
    return _as_int(s)


def _sniff_official_table(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Try to coerce an arbitrary ESPN CSV into:
      columns: week, fantasy_team_id, official_pts
    Returns None if not possible.
    """
    cols = {c.lower(): c for c in df.columns}

    # Candidate field names we might see
    team_id_keys = ["team_id", "teamid", "fantasy_team_id", "id"]
    week_keys = ["scoringperiodid", "week", "matchup_period_id"]
    points_keys = [
        "applied_total",
        "appliedtotal",
        "points",
        "total_points",
        "score",
        "final_score",
    ]

    def pick(keys: list[str]) -> str | None:
        for k in keys:
            if k in cols:
                return cols[k]
        return None

    team_col = pick(team_id_keys)
    week_col = pick(week_keys)
    pts_col = pick(points_keys)

    if team_col and week_col and pts_col:
        out = pd.DataFrame(
            {
                "fantasy_team_id": _norm_team_id(df[team_col]),
                "week": _norm_week(df[week_col]),
                "official_pts": _as_float(df[pts_col]).fillna(0.0),
            }
        )
        # Some files may contain multiple rows per team/week (home/away). Aggregate.
        out = out.groupby(["week", "fantasy_team_id"], as_index=False).agg(
            official_pts=("official_pts", "sum")
        )
        return out

    # Another pattern: matchups table with home/away blocks
    home_id = pick(["home_team_id", "hometeamid", "homeid"])
    away_id = pick(["away_team_id", "awayteamid", "awayid"])
    home_pts = pick(["home_total", "home_applied_total", "homesc", "home_score"])
    away_pts = pick(["away_total", "away_applied_total", "awaysc", "away_score"])
    week2 = pick(week_keys)

    if week2 and home_id and away_id and home_pts and away_pts:
        a = pd.DataFrame(
            {
                "fantasy_team_id": _norm_team_id(df[home_id]),
                "week": _norm_week(df[week2]),
                "official_pts": _as_float(df[home_pts]).fillna(0.0),
            }
        )
        b = pd.DataFrame(
            {
                "fantasy_team_id": _norm_team_id(df[away_id]),
                "week": _norm_week(df[week2]),
                "official_pts": _as_float(df[away_pts]).fillna(0.0),
            }
        )
        out = pd.concat([a, b], ignore_index=True)
        out = out.groupby(["week", "fantasy_team_id"], as_index=False).agg(
            official_pts=("official_pts", "sum")
        )
        return out

    return None


def _load_official(proc_dir: Path) -> pd.DataFrame:
    espn_dir = ESPN_DIR_TPL.with_name(ESPN_DIR_TPL.name).with_stem(ESPN_DIR_TPL.stem)
    espn_dir = Path(str(ESPN_DIR_TPL).format(season=proc_dir.name.split("_")[-1]))

    candidates = [
        "scoreboard.csv",
        "scoreboard_week.csv",
        "matchups.csv",
        "weekly_scores.csv",
        "team_scores.csv",
        "teams_week.csv",
        "teams.csv",  # last resort (if it has weekly breakdowns)
        "boxscores.csv",
    ]

    for name in candidates:
        p = espn_dir / name
        df = _read_csv(p)
        if df is None or df.empty:
            continue
        out = _sniff_official_table(df)
        if out is not None and not out.empty:
            print(f"ℹ️  Using official scores from: {p}")
            return out

    # If nothing found, raise a useful error
    raise SystemExit(
        f"No usable official scores found in {espn_dir}. "
        f"Tried: {', '.join(candidates)}. "
        f"Make sure a scoreboard/matchups export with team totals exists."
    )


def _load_ours(proc_dir: Path) -> pd.DataFrame:
    ours = _read_csv(proc_dir / "league_team_week_totals.csv")
    if ours is None or ours.empty:
        raise SystemExit(
            "Missing or empty league_team_week_totals.csv. Run join_league_points.py first."
        )
    need = {
        "season",
        "week",
        "fantasy_team_id",
        "fantasy_team_name",
        "pts_ppr_starters",
        "pts_ppr_all",
    }
    if not need.issubset(set(ours.columns)):
        raise SystemExit(f"league_team_week_totals.csv lacks columns: {sorted(need)}")
    ours["fantasy_team_id"] = _as_int(ours["fantasy_team_id"])
    ours["week"] = _as_int(ours["week"])
    # keep only relevant columns for comparison
    keep = [
        "season",
        "week",
        "fantasy_team_id",
        "fantasy_team_name",
        "pts_ppr_starters",
        "pts_ppr_all",
        "pts_pass_starters",
        "pts_rush_starters",
        "pts_rec_starters",
        "pts_kick_starters",
        "pts_misc_starters",
    ]
    keep = [c for c in keep if c in ours.columns]
    return ours[keep].copy()


def _hint_row(r: pd.Series) -> str:
    """
    Heuristic hints to speed up debugging deltas.
    """
    delta = r["delta_starters"]
    # if bench points would close the gap, we probably counted bench or vice-versa
    bench = r["pts_ppr_all"] - r["pts_ppr_starters"]
    if abs((r["pts_ppr_starters"] + bench) - r["official_pts"]) < 0.51:
        return "Likely bench/slot mismatch (bench explains delta)."
    # if kicking component is zero for us but official > ours by ~ a few points
    if "pts_kick_starters" in r and r["pts_kick_starters"] == 0 and delta > 0:
        return "Check kicker mapping/lineup slot; looks short on K points."
    # if misc is large negative/positive, might be turnovers/fumbles sign
    if (
        "pts_misc_starters" in r
        and abs(r["pts_misc_starters"]) >= 6
        and abs(delta) >= 6
    ):
        return "Turnover/fumble weights? Verify negative signs."
    return ""


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def main() -> None:
    season = _load_env_season()
    proc_dir = Path(str(PROC_TPL).format(season=season))

    ours = _load_ours(proc_dir)
    official = _load_official(proc_dir)

    # Join
    merged = ours.merge(
        official, on=["week", "fantasy_team_id"], how="left", validate="m:1"
    )

    if merged["official_pts"].isna().any():
        missing = merged[merged["official_pts"].isna()][
            ["week", "fantasy_team_id", "fantasy_team_name"]
        ]
        print("\n⚠️  Missing official totals for some team-weeks (showing up to 20):")
        print(missing.head(20).to_string(index=False))

    merged["delta_starters"] = (
        merged["pts_ppr_starters"] - merged["official_pts"]
    ).round(2)
    merged["delta_all"] = (merged["pts_ppr_all"] - merged["official_pts"]).round(2)

    # Hints
    merged["hint"] = merged.apply(_hint_row, axis=1)

    # Print per-week report sorted by |delta|
    weeks = sorted(merged["week"].dropna().unique())
    print("\n=== Official Parity (starters vs official) ===")
    for w in weeks:
        sub = merged[merged["week"] == w].copy()
        sub = sub.sort_values("delta_starters", key=lambda s: s.abs(), ascending=False)
        cols = [
            "season",
            "week",
            "fantasy_team_id",
            "fantasy_team_name",
            "pts_ppr_starters",
            "official_pts",
            "delta_starters",
            "pts_ppr_all",
            "delta_all",
            "hint",
        ]
        cols = [c for c in cols if c in sub.columns]
        print(f"\n-- Week {w} --")
        print(sub[cols].to_string(index=False))

    # Summary
    agg = (
        merged.groupby("week", dropna=False)
        .agg(
            teams=("fantasy_team_id", "nunique"),
            mean_abs_delta=("delta_starters", lambda s: float(s.abs().mean())),
            max_abs_delta=("delta_starters", lambda s: float(s.abs().max())),
            sum_abs_delta=("delta_starters", lambda s: float(s.abs().sum())),
        )
        .reset_index()
    )
    print("\n=== Summary (by week, starters only) ===")
    print(agg.to_string(index=False))

    # Save a CSV for diff triage
    out = proc_dir / "qc_official_parity.csv"
    merged.to_csv(out, index=False)
    print(f"\n✅ Wrote {out} (full joined diff).")


if __name__ == "__main__":
    main()
