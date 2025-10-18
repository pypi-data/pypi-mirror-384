# src/fppull/cli/env_refresh.py
"""
Auto-refresh ESPN cookies (SWID, espn_s2) from your local browser and
write them into the canonical .env used by fppull.

Usage:
  python -m fppull.cli.env_refresh           # auto-detect browser(s), write to canonical env
  python -m fppull.cli.env_refresh --dry-run # show what would be written
  python -m fppull.cli.env_refresh --path ./.env
  python -m fppull.cli.env_refresh --browser chrome
  python -m fppull.cli.env_refresh --browser firefox

Notes:
- Pure local operation. No network calls.
- Reads cookies from Chrome/Firefox login stores via browser_cookie3.
- Writes/updates SWID and ESPN_S2 in the resolved .env.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

# stdlib toml reader (Py3.11+)
try:
    import tomllib  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    tomllib = None  # py310 fallback if needed

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GLOBAL_ENV = Path.home() / ".config" / "fppull" / ".env"

SUPPORTED_BROWSERS = ("chrome", "firefox")


@dataclass
class CookiePair:
    swid: str
    espn_s2: str


def _mask(val: str, head: int = 6, tail: int = 4) -> str:
    if not val:
        return "(none)"
    if len(val) <= head + tail:
        return "*" * len(val)
    return f"{val[:head]}…{'*' * 4}"


def _read_pyproject_env_path() -> Optional[Path]:
    """If pyproject.toml contains [tool.fppull].env_file, return it."""
    pyproj = ROOT / "pyproject.toml"
    if not pyproj.is_file() or tomllib is None:
        return None
    try:
        data = tomllib.loads(pyproj.read_text(encoding="utf-8"))
        env_file = data.get("tool", {}).get("fppull", {}).get("env_file", "")
        if env_file:
            p = Path(env_file)
            return p if p.is_absolute() else (ROOT / p)
    except Exception:
        return None
    return None


def _resolve_env_path(cli_path: Optional[str]) -> Path:
    """Resolution order: CLI --path > pyproject > repo .env > global default."""
    if cli_path:
        return Path(cli_path).expanduser().resolve()
    p = _read_pyproject_env_path()
    if p:
        return p
    repo_env = ROOT / ".env"
    if repo_env.exists():
        return repo_env
    return DEFAULT_GLOBAL_ENV


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _gather_from_browser(browser: str) -> Dict[str, str]:
    """
    Load cookies for espn domains using browser_cookie3.
    Returns a dict {cookie_name: value, ...}.
    """
    try:
        import browser_cookie3  # noqa: E402 (local import to avoid hard dep at import time)
    except Exception as e:
        print(
            "ERROR: browser_cookie3 is not installed. Install with:\n"
            "  pip install browser-cookie3\n",
            file=sys.stderr,
        )
        raise SystemExit(1) from e

    loader = {
        "chrome": getattr(browser_cookie3, "chrome", None),
        "firefox": getattr(browser_cookie3, "firefox", None),
    }.get(browser)

    if loader is None:
        raise SystemExit(f"Unknown browser: {browser}")

    # Probe multiple domain scopes used by ESPN properties.
    jar = None
    domains = [
        ".espn.com",
        "espn.com",
        ".fantasy.espn.com",
        "fantasy.espn.com",
    ]
    for d in domains:
        try:
            cj = loader(domain_name=d)
            if jar is None:
                jar = cj
            else:
                # Merge: CookieJar behaves like iterable; add by name
                for c in cj:
                    jar.set_cookie(c)
        except Exception:
            # Ignore domain-specific failures; keep trying others
            continue

    cookies: Dict[str, str] = {}
    if jar:
        for c in jar:
            # normalize common names exactly as set by ESPN
            name_l = c.name.lower()
            if name_l in {"swid", "espn_s2"}:
                cookies[c.name] = c.value

    return cookies


def _discover_cookies(preferred: Optional[str] = None) -> CookiePair:
    """
    Try preferred browser first (if provided), then fall back to others.
    """
    order = []
    if preferred:
        order.append(preferred.lower())
    for b in SUPPORTED_BROWSERS:
        if b not in order:
            order.append(b)

    last_err = None
    for b in order:
        try:
            got = _gather_from_browser(b)
        except SystemExit:  # missing browser_cookie3 or other fatal
            raise
        except Exception as e:
            last_err = e
            continue

        swid = got.get("SWID") or got.get("swid") or ""
        s2 = got.get("espn_s2") or got.get("ESPN_S2") or ""
        if swid and s2:
            return CookiePair(swid=swid, espn_s2=s2)

    msg = "Could not find SWID/espn_s2 in supported browsers."
    if last_err:
        msg += f" Last error: {last_err}"
    raise SystemExit(msg)


_ENV_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _read_env_lines(path: Path) -> Dict[str, str]:
    """Parse a simple KEY=VALUE .env file (no export, no quotes expansion)."""
    out: Dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _ENV_LINE_RE.match(line)
        if m:
            key, val = m.group(1), m.group(2)
            out[key] = val
    return out


def _write_env(path: Path, kv: Dict[str, str]) -> None:
    """
    Upsert keys into .env, preserving other lines where possible.
    Writes atomically.
    """
    existing = _read_env_lines(path)
    existing.update(kv)

    # Reconstruct file, preserving unknown lines where possible
    lines = []
    seen = set()
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            m = _ENV_LINE_RE.match(raw)
            if m:
                k = m.group(1)
                if k in existing and k not in seen:
                    lines.append(f"{k}={existing[k]}")
                    seen.add(k)
                else:
                    # drop duplicate keys
                    if k not in existing:
                        lines.append(raw)
            else:
                lines.append(raw)

    # Append any keys not written yet
    for k, v in existing.items():
        if k not in seen:
            lines.append(f"{k}={v}")

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    tmp.replace(path)


def refresh(path_override: Optional[str], browser: Optional[str], dry_run: bool) -> int:
    env_path = _resolve_env_path(path_override)
    pair = _discover_cookies(browser)

    # Ensure SWID is quoted with braces when used in HTTP header;
    # but in .env we store the raw cookie values exactly as seen in the browser.
    # Downstream header builders will add quotes/braces as needed.
    kv = {
        "SWID": pair.swid,
        "ESPN_S2": pair.espn_s2,  # keep the exact (possibly percent-encoded) value
    }

    print("🔎 cookie refresh probe")
    print(f"  source  : {browser or 'auto'}")
    print(f"  SWID    : {_mask(pair.swid)}")
    print(f"  ESPN_S2 : {_mask(pair.espn_s2)}")
    print(f"  env_file: {env_path}")

    if dry_run:
        print("✅ dry-run: no changes written")
        return 0

    _ensure_parent(env_path)
    _write_env(env_path, kv)
    print("✅ wrote cookies to env file")
    print("   tip: git update-index --skip-worktree .env  # if repo-local")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh ESPN cookies into .env")
    parser.add_argument("--path", help="Write to this .env path (overrides resolution)")
    parser.add_argument(
        "--browser",
        choices=SUPPORTED_BROWSERS,
        help="Force a specific browser (default: auto-detect both)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show discovered values and target path without writing",
    )
    args = parser.parse_args(argv)

    return refresh(args.path, args.browser, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
