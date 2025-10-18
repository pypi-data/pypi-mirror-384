from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def _coverage_check(
    roster: pd.DataFrame,
    points: pd.DataFrame,
    roster_key: str = "player_id",
    points_key: str = "player_id",
) -> dict:
    """Minimal contract helper: what fraction of roster ids are present in points?
    Returns dict with: coverage (0..1), missing (count), missing_ids (sorted list)."""
    if roster_key not in roster.columns or points_key not in points.columns:
        return {"coverage": 0.0, "missing": 0, "missing_ids": []}

    r_ids = set(pd.to_numeric(roster[roster_key], errors="coerce").dropna().astype(int))
    p_ids = set(pd.to_numeric(points[points_key], errors="coerce").dropna().astype(int))

    missing_ids = sorted(r_ids - p_ids)
    coverage = (len(r_ids) - len(missing_ids)) / len(r_ids) if r_ids else 1.0

    return {
        "coverage": coverage,
        "missing": len(missing_ids),
        "missing_ids": missing_ids,
    }


TOL = 1e-6  # numeric tolerance for equality


def _read_csv(p: str | Path | None) -> pd.DataFrame | None:
    if not p:
        return None
    p = Path(p)
    if not p.exists():
        return None
    return pd.read_csv(p)


def _safe_float(v) -> float:
    try:
        return float(v)
    except Exception:
        return float("nan")


def _team_week_from_points(points: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    """Compute team/week totals by joining roster to points."""
    need = {"season", "week", "athlete_id"}
    if not need.issubset(points.columns) or not need.union(
        {"fantasy_team_id"}
    ).issubset(roster.columns):
        return pd.DataFrame(
            columns=["season", "week", "fantasy_team_id", "official_pts_total"]
        )

    joined = roster.merge(
        points[["season", "week", "athlete_id", "official_pts"]],
        on=["season", "week", "athlete_id"],
        how="left",
        validate="many_to_one",
    )
    g = (
        joined.groupby(["season", "week", "fantasy_team_id"], dropna=False)[
            "official_pts"
        ]
        .sum(min_count=1)
        .reset_index()
        .rename(columns={"official_pts": "official_pts_total"})
    )
    g["official_pts_total"] = g["official_pts_total"].fillna(0.0)
    return g


def build_report(
    points: pd.DataFrame,
    roster: pd.DataFrame,
    team_week: pd.DataFrame | None,
    league_summary: pd.DataFrame | None,
) -> dict:
    # ---- coverage / missing players
    need_roster = {"season", "week", "athlete_id"}
    need_points = {"season", "week", "athlete_id", "official_pts"}
    missing_players = None
    coverage_pct = None

    if need_roster.issubset(roster.columns) and need_points.issubset(points.columns):
        j = roster.merge(
            points[["season", "week", "athlete_id", "official_pts"]],
            on=["season", "week", "athlete_id"],
            how="left",
            validate="many_to_one",
        )
        total = len(j)
        covered = int(j["official_pts"].notna().sum())
        missing_players = int(total - covered)
        coverage_pct = round(100.0 * covered / total, 1) if total else 100.0
    else:
        missing_players = None
        coverage_pct = None

    # ---- team_week mismatches
    teamweek_mismatches = None
    if team_week is not None:
        if {"season", "week", "fantasy_team_id", "official_pts_total"}.issubset(
            team_week.columns
        ):
            calc_tw = _team_week_from_points(points, roster)
            if not calc_tw.empty:
                tw = team_week.copy()
                for col in ["official_pts_total"]:
                    tw[col] = tw[col].map(_safe_float)
                merged = tw.merge(
                    calc_tw,
                    on=["season", "week", "fantasy_team_id"],
                    how="outer",
                    suffixes=("_reported", "_calc"),
                    indicator=True,
                )
                merged["official_pts_total_reported"] = merged[
                    "official_pts_total_reported"
                ].fillna(0.0)
                merged["official_pts_total_calc"] = merged[
                    "official_pts_total_calc"
                ].fillna(0.0)
                diffs = (
                    merged["official_pts_total_reported"]
                    - merged["official_pts_total_calc"]
                ).abs()
                teamweek_mismatches = int((diffs > TOL).sum())
            else:
                teamweek_mismatches = None
        else:
            teamweek_mismatches = None

    # ---- league summary mismatches
    league_totals_mismatches = None
    if league_summary is not None:
        if {"season", "fantasy_team_id", "official_pts_total"}.issubset(
            league_summary.columns
        ):
            source_tw = team_week
            if source_tw is None or not {
                "season",
                "week",
                "fantasy_team_id",
                "official_pts_total",
            }.issubset(source_tw.columns):
                source_tw = _team_week_from_points(points, roster)
            agg = (
                source_tw.groupby(["season", "fantasy_team_id"], dropna=False)[
                    "official_pts_total"
                ]
                .sum(min_count=1)
                .reset_index()
                .rename(columns={"official_pts_total": "season_pts_total_calc"})
            )
            ls = league_summary.copy()
            ls["official_pts_total"] = ls["official_pts_total"].map(_safe_float)
            merged = ls.merge(
                agg,
                on=["season", "fantasy_team_id"],
                how="outer",
                suffixes=("_reported", "_calc"),
                indicator=True,
            )
            merged["official_pts_total"] = merged["official_pts_total"].fillna(0.0)
            merged["season_pts_total_calc"] = merged["season_pts_total_calc"].fillna(
                0.0
            )
            diffs = (
                merged["official_pts_total"] - merged["season_pts_total_calc"]
            ).abs()
            league_totals_mismatches = int((diffs > TOL).sum())
        else:
            league_totals_mismatches = None

    return {
        "coverage_pct": coverage_pct,
        "missing_players": missing_players,
        "teamweek_mismatches": teamweek_mismatches,
        "league_totals_mismatches": league_totals_mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("entry", nargs="?", help="unused shim to match tests (ENTRY)")
    ap.add_argument("--points", required=True)
    ap.add_argument("--roster", required=True)
    ap.add_argument("--team-week", dest="team_week")
    ap.add_argument("--league-summary", dest="league_summary")
    ap.add_argument("--out-report", required=True)
    args = ap.parse_args(argv)

    points = _read_csv(args.points)
    if points is None:
        points = pd.DataFrame()
    roster = _read_csv(args.roster)
    if roster is None:
        roster = pd.DataFrame()
    team_week = _read_csv(args.team_week) if args.team_week else None
    league_summary = _read_csv(args.league_summary) if args.league_summary else None

    report = build_report(points, roster, team_week, league_summary)

    out = Path(args.out_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True))

    # Exit 1 if any concrete error counts are > 0
    bad = 0
    for key in ("missing_players", "teamweek_mismatches", "league_totals_mismatches"):
        val = report.get(key)
        if isinstance(val, int) and val > 0:
            bad = 1
            break

    return bad


if __name__ == "__main__":
    raise SystemExit(main())
