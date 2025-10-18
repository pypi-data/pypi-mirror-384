from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from fppull.cli.pull_week import load_stats_offline
from fppull.join_reports import join_roster_and_stats
from fppull.private_league import fetch_roster_df


@dataclass(frozen=True)
class AggregationResult:
    weeks: list[int]
    joined: pd.DataFrame


def join_all_weeks(season: int, weeks: Iterable[int]) -> AggregationResult:
    """Join roster with weekly stats across multiple weeks (offline-safe).

    Expects sample weekly stats at:
      data/samples/week_{season}_{WW}_stats.csv  (WW = zero-padded week)
    And a roster source via private_league.fetch_roster_df(season, ...)

    Returns a DataFrame that includes at least:
      ['season','week','team_id','team_name','player_id','position', 'points' ...]
    """
    wk_list = sorted({int(w) for w in weeks})
    roster = fetch_roster_df(season)

    frames: list[pd.DataFrame] = []
    for w in wk_list:
        stats = load_stats_offline(season, w)
        joined = join_roster_and_stats(roster, stats, season=season, week=w)
        frames.append(joined)

    if not frames:
        return AggregationResult([], pd.DataFrame())

    out = pd.concat(frames, ignore_index=True)

    # Basic hygiene
    # - ensure explicit season/week columns exist
    if "season" not in out.columns:
        out["season"] = season
    if "week" not in out.columns:
        # trust the per-week joins added it; if not, set NA (shouldn't happen)
        out["week"] = pd.NA

    # - sort for stable output
    sort_cols = [
        c for c in ["season", "week", "team_id", "player_id"] if c in out.columns
    ]
    if sort_cols:
        out = out.sort_values(sort_cols, kind="stable").reset_index(drop=True)

    return AggregationResult(wk_list, out)


def write_season_outputs(
    df: pd.DataFrame, season: int, out_dir: str | Path = "data/processed"
) -> dict[str, str]:
    """Write season aggregates to CSV and Parquet, return written paths."""
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    csv_path = outp / f"season_{season}_joined.csv"
    parquet_path = outp / f"season_{season}_joined.parquet"
    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(parquet_path, index=False)
    except Exception:
        # parquet is optional locally
        parquet_path = ""
    return {"csv": str(csv_path), "parquet": str(parquet_path) if parquet_path else ""}
