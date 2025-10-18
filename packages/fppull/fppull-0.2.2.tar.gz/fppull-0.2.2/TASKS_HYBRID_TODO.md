# Hybrid Tasks (finish line)

## 1) Compute fantasy points from public stats
- [ ] Ensure `src/fppull/compute_points.py` reads `player_week_stats_wide.csv` and writes `player_week_points.csv`
- Quick run:
```bash
PYTHONPATH=src python -m src.fppull.compute_points \
  --season 2025 \
  --in data/processed/season_2025/player_week_stats_wide.csv \
  --out data/processed/season_2025/player_week_points.csv


- [x] Compute player_week_points.csv
- [x] Build team_week_points.csv via join

- [x] Export analysis workbook (XLSX)
