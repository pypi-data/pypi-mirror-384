# src/fppull/cli/calc_points_from_joined.py
import argparse
from pathlib import Path

import pandas as pd


def _load_scoring(scoring_csv: Path) -> dict[int, float]:
    """
    Minimal map from ESPN statId -> points. Unknowns default to 0 in calc.
    """
    df = pd.read_csv(scoring_csv)
    # tolerate files that have extra columns
    if "statId" not in df.columns or "points" not in df.columns:
        raise SystemExit(f"Scoring file missing columns statId/points: {scoring_csv}")
    m = {}
    for _, r in df.iterrows():
        sid = int(r["statId"])
        pts = float(r.get("points", 0) or 0)
        m[sid] = pts
    return m


def _compute_points(row: pd.Series) -> float:
    """
    Simple linear scoring using common columns if present.
    Extend as needed; missing fields contribute 0.
    """
    v = 0.0
    # Passing
    v += (row.get("pass_yds", 0) or 0) * 0.04
    v += (row.get("pass_td", 0) or 0) * 4.0
    v += (row.get("pass_int", 0) or 0) * -2.0
    # Rushing
    v += (row.get("rush_yds", 0) or 0) * 0.1
    v += (row.get("rush_td", 0) or 0) * 6.0
    # Receiving
    v += (
        row.get("rec_rec", 0) or 0
    ) * 1.0  # PPR default; adjust if your league differs
    v += (row.get("rec_yds", 0) or 0) * 0.1
    v += (row.get("rec_td", 0) or 0) * 6.0
    # Fumbles
    v += (row.get("fum_lost", 0) or 0) * -2.0
    # Kicking (coarse)
    v += (row.get("k_fgm", 0) or 0) * 3.0
    v += (row.get("xp_made", 0) or 0) * 1.0
    return float(v)


def main():
    p = argparse.ArgumentParser(description="Compute fantasy points for joined CSV.")
    # Prefer --input, keep --in as alias for compatibility
    p.add_argument("--input", dest="inp", required=False, help="Input joined CSV path")
    p.add_argument("--in", dest="inp", required=False, help=argparse.SUPPRESS)
    p.add_argument("--season", type=int, required=True)
    p.add_argument(
        "--scoring",
        type=Path,
        required=False,
        help="Path to scoring_table.csv (if omitted, resolve from --season)",
    )
    p.add_argument("--out", dest="outp", type=Path, required=True)
    args = p.parse_args()

    inp = Path(args.inp) if args.inp else None
    if not inp:
        raise SystemExit("Input not provided. Use --input PATH")
    if not inp.is_file():
        cwd = Path.cwd()
        raise SystemExit(f"Input not found: {inp} (cwd={cwd})")

    scoring = args.scoring
    if not scoring:
        scoring = Path(f"data/processed/season_{args.season}/espn/scoring_table.csv")
    if not scoring.is_file():
        raise SystemExit(f"Could not locate scoring table: {scoring}")

    # Load input and compute fantasy points
    df = pd.read_csv(inp)
    df["points"] = df.apply(_compute_points, axis=1)

    # Ensure no missing values propagate to disk
    df["points"] = df["points"].fillna(0.0)

    # Write output CSV
    args.outp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.outp, index=False)
    print(f"✅ wrote {args.outp} with {len(df)} rows and 'points' column")


if __name__ == "__main__":
    main()
