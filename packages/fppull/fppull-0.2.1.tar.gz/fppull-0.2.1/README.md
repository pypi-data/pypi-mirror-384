[![Stable release](https://img.shields.io/badge/stable-v1.0.0-brightgreen)](https://github.com/Masen222/fantasy-public-pull/releases/tag/v1.0.0)

> **Roadmap:** We are on **A) Hybrid** → see [ROADMAP.md](./ROADMAP.md).  
> **Releases:** see [RELEASING.md](./RELEASING.md).


> **Roadmap:** Currently on **A) Hybrid**. See [ROADMAP.md](./ROADMAP.md).

[![PyPI](https://img.shields.io/pypi/v/fppull.svg)](https://pypi.org/project/fppull/)
[![Python versions](https://img.shields.io/pypi/pyversions/fppull)](https://pypi.org/project/fppull/)
[![CI](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml)
[![Release workflow](https://github.com/Masen222/fantasy-public-pull/actions/workflows/release-on-tag.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/release-on-tag.yml)
[![PyPI publish](https://github.com/Masen222/fantasy-public-pull/actions/workflows/publish-pypi.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/publish-pypi.yml)

[![CI](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml)

[![CI](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml)

> **Status:** Continuous Integration (contracts + validation checks) passing ✅

# fantasy-public-pull

Goal: Use ESPN **private** league endpoints only to discover league/team/roster, and use **public** endpoints to fetch week-by-week player stats for *all players* (regardless of roster), then join them when building reports.

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdir -p data/raw data/processed
# place raw pulls in data/raw ; clean outputs go to data/processed
```

## Local Development Safety Checks

This repo uses a shared `.githooks/pre-push` script to enforce style, lint, and contract tests **before every push**.

### One-time setup per machine
```bash
# ensure hooks use the shared folder
git config core.hooksPath .githooks

# install pre-commit into your virtualenv (if not already)
pip install pre-commit

# (optional) verify everything runs cleanly
git commit --allow-empty -m "hook check"
git push
```

## Docs

- See the full [Documentation Index](./docs/README.md) for developer setup, CLI usage, roadmap, and releasing.


### Local guardrails (pre-push)
```bash
pip install -r requirements-dev.txt
git config core.hooksPath .githooks
# (optional) run once to build hook envs faster:
pre-commit run --all-files
```

The pre-push hook runs:
- `pre-commit` (Black + Ruff) on your changes  
- `./scripts/ci.sh test` (unit tests)  
- `./scripts/ci.sh contracts` (contract tests)  

Pushes are blocked if any step fails.
## Reports

Once you’ve generated a joined season file (e.g., with `pull_range`), you can summarize it:

```bash
# regenerate joined data (offline sample weeks 1–3)
python -m fppull.cli.pull_range --season 2025 --weeks 1-3 --out-dir data/processed

# top players by total points
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --top 15

# group by position
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --group-by position --top 10

# group by team
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --group-by team --top 10

# require a minimum number of distinct weeks (e.g., >= 2)
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --group-by player --min-weeks 2 --top 20

# optionally write the table to CSV
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --group-by team --out data/processed/top_teams.csv


## Make targets

Handy shortcuts for common tasks:

```bash
# Rebuild joined data and print a top summary (defaults: season=2025, weeks=1-3)
make report-top

# Variations:
make report-top season=2025 weeks=1-3
make report-top season=2025 group_by=team top=10
make report-top season=2025 group_by=position min_weeks=2

# Local checks
make test         # unit tests
make contracts    # contract tests
make lint         # ruff
make fmt          # black
make ci           # fmt + lint + tests + contracts

### report_top formats & PPG

```bash
# table (default) + points per game
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --top 10 --ppg

# CSV to stdout
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --format csv --top 10

# JSON to file
python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --format json --ppg --top 10 --out data/processed/top10.json

[![PyPI version](https://img.shields.io/pypi/v/fppull.svg)](https://pypi.org/project/fppull/)
[![Release](https://img.shields.io/github/v/release/Masen222/fantasy-public-pull?display_name=tag)](https://github.com/Masen222/fantasy-public-pull/releases)
[![CI](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml/badge.svg)](https://github.com/Masen222/fantasy-public-pull/actions/workflows/ci.yml)

## Install

```bash
pip install fppull
```


## Artifacts map (what gets produced)

| Layer | How to run | Key outputs |
|------|------------|-------------|
| Public stats | `python -m fppull.cli.pull_range --season 2025 --weeks 1-3 --out-dir data/processed` | `player_week_stats_long.csv`, `player_week_stats_wide.csv`, **`player_week_points.csv`** |
| Private league context | (your private fetch or CSVs) | `teams.csv`, `roster_week.csv`, `matchups.csv` |
| Join + reports | `python -m fppull.cli.report_top --in data/processed/season_2025_joined.csv --top 15 [--group-by position|team]` | console table (or `--out` CSV/JSON), league workbook (optional) |
