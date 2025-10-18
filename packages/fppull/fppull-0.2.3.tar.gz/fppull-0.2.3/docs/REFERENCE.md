# Developer Reference

## CLI Modules

| Command | Description | Example |
|----------|-------------|----------|
| `fppull.cli.pull_range` | Pull public ESPN player stats for a season/week range | `python -m fppull.cli.pull_range --season 2025 --weeks 1-3 --out-dir data/processed` |
| `fppull.cli.report_top` | Summarize joined data (points by player/team/position) | `python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --top 15` |

## Data Layers

| Layer | Purpose | Example Outputs |
|--------|----------|-----------------|
| Public stats | Authoritative player week data | `player_week_stats_long.csv`, `player_week_points.csv` |
| Private league context | Roster + team metadata | `teams.csv`, `roster_week.csv`, `matchups.csv` |
| Join layer | Combined analytics data | `team_week_points.csv`, `League_Analysis.xlsx` |

## Notes
- All CLI modules are import-safe (may be used as library entrypoints).
- Consistent CSV schemas enforced via tests in `tests/contract/`.
