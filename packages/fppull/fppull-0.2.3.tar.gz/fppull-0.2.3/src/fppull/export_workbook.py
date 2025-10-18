import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"

TABS = [
    ("Player_Week_Points", "player_week_points.csv"),
    ("Roster_Week", "private/roster_week.csv"),
    ("Teams", "private/teams.csv"),
    ("Matchups", "private/matchups.csv"),
    ("Team_Week_Points", "team_week_points.csv"),  # we just created this
    (
        "League_Team_Totals",
        "league_team_week_totals.csv",
    ),  # canonical name we wrote earlier
]


def main():
    p = argparse.ArgumentParser(
        description="Export analysis workbook (XLSX) from processed CSVs"
    )
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--out", type=str, default=None, help="Optional output path")
    args = p.parse_args()

    out_dir = PROC / f"season_{args.season}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_xlsx = Path(args.out) if args.out else (out_dir / "League_Analysis.xlsx")

    with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as xl:
        wrote_any = False
        for tab_name, rel in TABS:
            csv_path = out_dir / rel
            if csv_path.exists():
                try:
                    df = pd.read_csv(csv_path)
                except Exception:
                    # some CSVs (like league_team_week_totals) are already clean; fallback to read_table if needed
                    df = pd.read_table(csv_path, sep=",")
                df.to_excel(xl, sheet_name=tab_name, index=False)
                wrote_any = True
        if not wrote_any:
            raise SystemExit("No input CSVs found; run the compute/join steps first.")

    print(f"✅ Wrote {out_xlsx}")


if __name__ == "__main__":
    main()
