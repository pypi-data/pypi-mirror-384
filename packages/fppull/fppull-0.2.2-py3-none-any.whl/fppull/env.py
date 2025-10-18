# src/fppull/env.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import tomllib  # py311+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

DEFAULT_ENV_FILE = Path.home() / ".config" / "fppull" / ".env"


@dataclass
class CookieConfig:
    source: Optional[Path]
    swid: Optional[str]
    espn_s2: Optional[str]


def _read_pyproject_env_path(repo_root: Path) -> Optional[Path]:
    py = repo_root / "pyproject.toml"
    if not py.exists() or tomllib is None:
        return None
    try:
        data = tomllib.loads(py.read_text())
        path = data.get("tool", {}).get("fppull", {}).get("env_file")
        if path:
            p = Path(path).expanduser()
            return (
                p if p.exists() else p
            )  # return even if missing (we may want to create it)
    except Exception:
        pass
    return None


def _mask(token: Optional[str], keep: int = 6) -> Optional[str]:
    if not token:
        return None
    if len(token) <= keep:
        return "*" * len(token)
    return token[:keep] + "…" + "*" * max(0, len(token) - keep - 1)


def discover_env_file(repo_root: Optional[Path] = None) -> Path:
    """
    Resolution order for where cookies live:
      1) pyproject.toml [tool.fppull].env_file (if set)
      2) repo-local .env (if exists)
      3) ~/.config/fppull/.env  (canonical default)
    """
    repo_root = repo_root or Path.cwd()

    # 1) pyproject override
    p = _read_pyproject_env_path(repo_root)
    if p:
        return p

    # 2) repo-local .env
    local = repo_root / ".env"
    if local.exists():
        return local

    # 3) default
    return DEFAULT_ENV_FILE


def read_cookies(repo_root: Optional[Path] = None) -> CookieConfig:
    """
    Load ESPN cookies from (a) process env or (b) resolved .env file.
    Returns CookieConfig with masked-print helpers handled by caller.
    """
    # From process env first
    swid_env = os.getenv("SWID")
    s2_env = os.getenv("ESPN_S2")

    env_file = discover_env_file(repo_root)
    swid_file = None
    s2_file = None

    if env_file.exists():
        # Manual parse to avoid adding a runtime dependency
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("SWID=") and swid_env is None:
                swid_file = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("ESPN_S2=") and s2_env is None:
                s2_file = line.split("=", 1)[1].strip().strip('"').strip("'")

    swid = swid_env or swid_file
    s2 = s2_env or s2_file

    return CookieConfig(source=env_file if env_file else None, swid=swid, espn_s2=s2)


def ensure_env_dir(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def write_cookies(path: Path, swid: str, espn_s2: str) -> None:
    ensure_env_dir(path)
    content = [
        "# ESPN private cookie values",
        "ESPN_S2=" + espn_s2,
        "SWID=" + swid,
        "",
    ]
    path.write_text("\n".join(content))
