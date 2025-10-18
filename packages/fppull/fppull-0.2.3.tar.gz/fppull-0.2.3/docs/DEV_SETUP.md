# Developer Quickstart

## Environment setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

## Local validation
Before pushing:
```bash
pre-commit run --all-files
make ci
```

## One-line reset
If your pre-commit hook breaks:
```bash
rm -rf ~/.cache/pre-commit && pre-commit clean && pre-commit install
```
---

## Environment configuration (ESPN cookies)

Private ESPN league access requires two cookie values: `ESPN_S2` and `SWID`.

You can set them permanently via `.env` in your repo root or globally under
`~/.config/fppull/.env`. The repo’s canonical location is declared in
`pyproject.toml` under `[tool.fppull].env_file`.

### 1. Create or update `.env`

```bash
# .env (example)
ESPN_S2=AEBx0SLPPq8tFRfau40I6r8WQj2G8kfCTBtiu4re...
SWID={9E64FE7A-B786-4A4A-A4FE-7AB786EA4A97}

# Developer Quickstart

## Environment setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install