#!/usr/bin/env bash
set -euo pipefail

season=${1:-2025}
weeks=${2:-1-3}
outdir=data/processed

# Rebuild joined data (offline-safe)
python -m src.fppull.cli.pull_range --season "$season" --weeks "$weeks" --out-dir "$outdir"

# Show top players by points
python -m src.fppull.cli.report_top --in "$outdir/season_${season}_joined.csv" --top 15
