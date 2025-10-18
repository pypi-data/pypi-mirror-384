# src/fppull/cli/env.py
from __future__ import annotations

import argparse
from pathlib import Path

from fppull.env import read_cookies, discover_env_file, write_cookies, _mask


def _print_doctor(repo_root: Path) -> int:
    cfg = read_cookies(repo_root)
    where = cfg.source or discover_env_file(repo_root)
    print("🔎 fppull env doctor")
    print(f"  repo_root: {repo_root}")
    print(f"  env_file : {where} {'(exists)' if where.exists() else '(will create)'}")
    print(f"  SWID     : {(_mask(cfg.swid) or 'MISSING')}")
    print(f"  ESPN_S2  : {(_mask(cfg.espn_s2) or 'MISSING')}")
    if not (cfg.swid and cfg.espn_s2):
        print("\n❌ Missing values. To set them:")
        print(
            f"  python -m fppull.cli.env write --path '{where}' "
            "--swid '{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}' "
            "--espn-s2 '<paste-from-cookie>'"
        )
        return 1
    print("\n✅ Cookies discovered. You’re good to go.")
    return 0


def _write(path: Path, swid: str, espn_s2: str) -> int:
    write_cookies(path, swid, espn_s2)
    print(f"✅ Wrote cookies to {path}")
    print("   Tip: `git update-index --skip-worktree .env` if you keep it repo-local.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="fppull env",
        description="Manage ESPN cookie env for fppull",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("doctor", help="Show cookie file and whether values are set")
    p1.add_argument("--repo-root", default=".", type=Path)

    p2 = sub.add_parser("where", help="Print the resolved .env path")
    p2.add_argument("--repo-root", default=".", type=Path)

    p3 = sub.add_parser("write", help="Write SWID and ESPN_S2 to the env file")
    p3.add_argument("--path", type=Path)
    p3.add_argument(
        "--swid", required=True, help="e.g. {9E64FE7A-B786-4A4A-A4FE-7AB786EA4A97}"
    )
    p3.add_argument("--espn-s2", required=True, help="long cookie value from browser")

    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        return _print_doctor(args.repo_root.resolve())
    if args.cmd == "where":
        path = discover_env_file(args.repo_root.resolve())
        print(path)
        return 0
    if args.cmd == "write":
        path = args.path or discover_env_file(Path.cwd())
        return _write(path, args.swid, args.espn_s2)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
