from __future__ import annotations

import argparse
from collections.abc import Sequence

from fppull.aggregate_season import join_all_weeks, write_season_outputs


def parse_weeks(raw: str) -> list[int]:
    """Accept '1,2,3' or '1-3' or mixed '1,2,5-6'."""
    weeks: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            weeks.extend(range(int(a), int(b) + 1))
        else:
            weeks.append(int(part))
    return sorted(set(weeks))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Join roster + weekly stats for a range of weeks (offline)."
    )
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--weeks", type=str, required=True, help="e.g., '1-3' or '1,2,3'")
    ap.add_argument(
        "--out-dir",
        default="data/processed",
        help="Output directory (default: data/processed)",
    )
    args = ap.parse_args(argv)

    weeks = parse_weeks(args.weeks)
    result = join_all_weeks(args.season, weeks)
    paths = write_season_outputs(
        result.joined, season=args.season, out_dir=args.out_dir
    )
    print(
        f"✅ joined {len(result.weeks)} weeks -> {paths['csv']}"
        + (f" & {paths['parquet']}" if paths["parquet"] else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
