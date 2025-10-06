#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import pandas as pd

def label_for_year(year:int)->str:
    return f"{year-1}-{str(year)[-2:]}"

def write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    label = label_for_year(args.year)
    outdir = root / "schema" / label
    outdir.mkdir(parents=True, exist_ok=True)

    # Ratings master
    m = root / "statewide" / f"SchoolRatings_MASTER_{label}.csv"
    if m.exists():
        cols = pd.read_csv(m, nrows=0, dtype=str).columns.tolist()
        write_json(outdir/"ratings_master_headers.json", {"file": m.name, "columns": cols})

    # Enrollment preview
    e = root / "data" / "enrollment" / f"{label}_preview.csv"
    if e.exists():
        cols = pd.read_csv(e, nrows=0, dtype=str).columns.tolist()
        write_json(outdir/"enrollment_preview_headers.json", {"file": e.name, "columns": cols})

    # Disaggregated dir listing (just file names present)
    ddir = root / "data" / "nspf-disagg" / label
    if ddir.exists():
        files = sorted([p.name for p in ddir.glob("*") if p.is_file()])
        write_json(outdir/"disagg_file_list.json", {"dir": str(ddir), "files": files})

    print(f"Wrote header snapshots under {outdir}")

if __name__ == "__main__":
    main()
