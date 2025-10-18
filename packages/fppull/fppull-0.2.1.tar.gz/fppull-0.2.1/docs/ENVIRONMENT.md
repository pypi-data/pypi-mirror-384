# Environment configuration (ESPN cookies)

Private ESPN league endpoints require two cookies: `ESPN_S2` and `SWID`.

## Canonical location

- Default: `~/.config/fppull/.env`
- Optional override: set `[tool.fppull].env_file` in `pyproject.toml`
- Repo-local `.env` is also supported if present.

**Resolution order**:
1. `pyproject.toml` → `[tool.fppull].env_file`
2. repo-local `.env`
3. `~/.config/fppull/.env` (default)

## One-time setup

```bash
# See where fppull expects your env file:
python -m fppull.cli.env where

# Write values (safe, idempotent):
python -m fppull.cli.env write \
  --swid '{9E64FE7A-B786-4A4A-A4FE-7AB786EA4A97}' \
  --espn-s2 '<paste-from-browser-cookie>'
# (omit --path to use the canonical location; add --path ./.env to keep it repo-local)

---

## Verify and troubleshoot

### Check configuration
```bash
python -m fppull.cli.env doctor