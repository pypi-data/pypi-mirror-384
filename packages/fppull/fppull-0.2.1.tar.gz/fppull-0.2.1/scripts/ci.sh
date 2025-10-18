#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"  # avoid unbound var warnings

cmd="${1:-}"; shift || true
case "$cmd" in
  fmt)        black src tests ;;
  lint)       ruff check src tests ;;
  test)       PYTHONPATH=src pytest -q ;;
  contracts)  pytest -q tests/contract ;;
  validate-ci)
    mkdir -p data/processed
    python -m src.fppull.validate_join_analysis validate \
      --points tests/fixtures/ci/points.csv \
      --roster tests/fixtures/ci/roster.csv \
      --team-week tests/fixtures/ci/team_week.csv \
      --league-summary tests/fixtures/ci/league_summary.csv \
      --out-report data/processed/validation_report.json
    ;;
  ci-status)
    : "${OWNER:?set OWNER}"; : "${REPO:?set REPO}"; : "${RUN_ID:?set RUN_ID}"; : "${GITHUB_TOKEN:?set GITHUB_TOKEN}"
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID" |
      python3 -c 'import sys,json; d=json.load(sys.stdin); print("status:", d.get("status")); print("conclusion:", d.get("conclusion")); print("html:", d.get("html_url"))'
    ;;
  ci-jobs)
    : "${OWNER:?set OWNER}"; : "${REPO:?set REPO}"; : "${RUN_ID:?set RUN_ID}"; : "${GITHUB_TOKEN:?set GITHUB_TOKEN}"
    curl -sS -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$OWNER/$REPO/actions/runs/$RUN_ID/jobs?per_page=100" |
      python3 - "$@" <<'PY'
import json, sys
d = json.load(sys.stdin) or {}
print("found jobs:", d.get("total_count"))
for j in d.get("jobs", []):
    print(f"- {j.get('name')}: {j.get('status')} / {j.get('conclusion')} | {j.get('html_url')}")
PY
    ;;
  *) echo "Usage: scripts/ci.sh {fmt|lint|test|contracts|validate-ci|ci-status|ci-jobs}"; exit 2 ;;
esac
