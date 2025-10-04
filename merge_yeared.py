#!/usr/bin/env python3
import pandas as pd, glob, re, os, json, argparse
from pathlib import Path

def acad_label(y: int) -> str:
    return f"{y-1}-{str(y)[-2:]}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True, help="Column year (e.g., 2024 for 2023-24)")
    ap.add_argument("--indir", default="downloads", help="Base downloads dir")
    ap.add_argument("--outdir", default="statewide")
    ap.add_argument("--ids", default="out/district_ids.json")
    ap.add_argument("--excel", action="store_true", help="Also write an .xlsx if openpyxl is available")
    args = ap.parse_args()

    label = acad_label(args.year)
    folder = Path(args.indir) / str(args.year)
    files = sorted(folder.glob("SchoolRatings_*.csv"))
    if not files:
        raise SystemExit(f"No CSVs found in {folder}")

    ids_map = {str(x["district_id"]): x["district_name"] for x in json.load(open(args.ids, "r", encoding="utf-8"))}

    dfs = []
    for fp in files:
        name = os.path.basename(fp)
        m = re.search(r"SchoolRatings_(?:\d{4}-\d{2}_)?(\d+)_", name)
        did = m.group(1) if m else None
        df = pd.read_csv(fp)
        df["district_id"] = did
        df["district_name"] = ids_map.get(did)
        df["year"] = args.year
        dfs.append(df)

    out = pd.concat(dfs, ignore_index=True, sort=False)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    outcsv = outdir / f"SchoolRatings_MASTER_{label}.csv"
    out.to_csv(outcsv, index=False)
    print(f"Wrote {outcsv}  ({len(out)} rows, {len(out.columns)} cols)")

    if args.excel:
        try:
            import openpyxl  # noqa: F401
            outxlsx = outdir / f"SchoolRatings_MASTER_{label}.xlsx"
            out.to_excel(outxlsx, index=False)
            print(f"Wrote {outxlsx}")
        except Exception as e:
            print(f"[INFO] Skipped Excel (install openpyxl to enable): {e}")

if __name__ == "__main__":
    main()
