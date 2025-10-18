# ---- sane defaults ----
.DEFAULT_GOAL := help
SHELL := /bin/bash
.ONESHELL:

# Parameters (overridable: `make report-top season=2025 weeks=1-3`)
season    ?= 2025
weeks     ?= 1-3
outdir    ?= data/processed
group_by  ?= player
min_weeks ?= 0
top       ?= 15
ppg       ?= 0
format    ?= table
out       ?=

# ---- phony targets ----
.PHONY: help report-top test contracts lint fmt ci

help:
	@echo "Targets:"
	@echo "  report-top        Rebuild joined data and print a top summary"
	@echo "  test              Run unit tests"
	@echo "  contracts         Run contract tests"
	@echo "  lint              Run ruff"
	@echo "  fmt               Run black"
	@echo "  ci                Run local CI (fmt, lint, tests, contracts)"
	@echo
	@echo "Examples:"
	@echo "  make report-top season=2025 weeks=1-3"
	@echo "  make report-top season=2025 group_by=team top=10"
	@echo "  make report-top season=2025 group_by=position min_weeks=2"

report-top:
	python -m src.fppull.cli.pull_range --season $(season) --weeks $(weeks) --out-dir $(outdir)
	python -m src.fppull.cli.report_top \
		--in $(outdir)/season_$(season)_joined.csv \
		--group-by $(group_by) \
		--min-weeks $(min_weeks) \
		--top $(top) \
		$(if $(filter 1,$(ppg)),--ppg,) \
		--format $(format) \
		$(if $(out),--out $(out),)
