# Contributing

Thanks for helping improve **fantasy-public-pull**!

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

### Local build byproducts
We ignore `*.egg-info/` and `src/fppull.egg-info/`.  
If these appear in `git status`, run:
```bash
git rm -r --cached src/fppull.egg-info 2>/dev/null || true

### Local build byproducts

We ignore `*.egg-info/` and `src/fppull.egg-info/`.

If these show up in `git status`, clean them and recommit:

```bash
git rm -r --cached src/fppull.egg-info 2>/dev/null || true
git rm -r --cached *.egg-info          2>/dev/null || true
git add .gitignore
git commit -m "chore: ignore egg-info"

```
