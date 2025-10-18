from __future__ import annotations

import os

import pandas as pd

# Expose fetch_roster_df at module scope so tests can monkeypatch it:
from .private_league import fetch_roster_df  # noqa: F401


def join_roster_and_stats(
    roster_or_season,
    stats_df: pd.DataFrame,
    *,
    season: int | None = None,
    week: int | None = None,
) -> pd.DataFrame:
    """
    Join roster with weekly stats.

    Back-compat:
      - Old style: join_roster_and_stats(2025, stats_df)
        (season first; roster fetched via private_league.fetch_roster_df)
      - New style: join_roster_and_stats(roster_df, stats_df, *, season=..., week=...)
    """
    # Determine roster_df and season based on call style
    if isinstance(roster_or_season, int) and season is None:
        season = roster_or_season
        league_id = os.getenv("LEAGUE_ID")
        roster_df = fetch_roster_df(season=season, league_id=league_id)
    else:
        roster_df = roster_or_season

    # Validate inputs
    for col in ("player_id",):
        if col not in getattr(roster_df, "columns", []):
            raise ValueError("roster_df must include column 'player_id'")
        if col not in getattr(stats_df, "columns", []):
            raise ValueError("stats_df must include column 'player_id'")

    out = roster_df.merge(stats_df, on="player_id", how="left")

    # Normalize overlapping columns: prefer roster's values
    # e.g., position_x/position_y -> position; also handle team_id_x/_y, team_name_x/_y
    if "position_x" in out.columns:
        out = out.rename(columns={"position_x": "position"})
        if "position_y" in out.columns:
            out = out.drop(columns=["position_y"])
    for base in ("team_id", "team_name"):
        x, y = f"{base}_x", f"{base}_y"
        if x in out.columns:
            out = out.rename(columns={x: base})
            if y in out.columns:
                out = out.drop(columns=[y])

    # Stamp metadata if provided
    if season is not None:
        out["season"] = int(season)
    if week is not None:
        out["week"] = int(week)

    return out
