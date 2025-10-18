# Roadmap

## A) Hybrid (Public stats + your league context) — **ACTIVE NOW**
**Goal:** Use public ESPN game data to compute authoritative per-player points for every week, then layer in your private ESPN league context (teams/rosters/matchups) for analytics (z-scores, trades, team totals).

### Data layers
- **Public stats (source of truth for points):** scoreboard + summary → `player_week_stats_long.csv`, `player_week_stats_wide.csv`, **`player_week_points.csv`**
- **Private league context (no stats):** `teams.csv`, `roster_week.csv`, `matchups.csv`
- **Join layer:** `team_week_points.csv`, `player_unowned_points.csv` (optional), matchup sums (optional)
- **Delivery:** **`League_Analysis.xlsx`** (optional)

### Minimal validation
- Coverage check: all `(season, week, athlete_id)` from wide have a joined row after roster merge. Emit `player_missing_points.csv` if not.
- Optional parity: sum starters vs official team score (sanity only).

---

## B) Full-Coverage (League-driven scorer: IDP, DST, bonuses, guardrails) — **UPGRADE LATER**
**Goal:** Reproduce ESPN scoring 1:1 across all positions/bonuses for any ESPN league, with strong QC and CI.

### Highlights vs Hybrid
- Read league `scoring_table.csv`; enforce a **schema contract** (fail fast on gaps).
- Add **IDP (slot 17)** and **DST (slot 16)**; **kicker distance buckets + misses**; **2-pt conversions + yard/TD bonuses**.
- Three-tier QC: per-player, team starters vs official, per-slot coverage map; CI + pytest.

### Why keep both?
- **Hybrid** → fastest path to useful analytics.
- **Full-Coverage** → maximum correctness & portability.

