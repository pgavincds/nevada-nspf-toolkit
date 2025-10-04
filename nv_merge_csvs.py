#!/usr/bin/env python3
"""
Merge all downloaded district-level SchoolRatings CSVs into one master file.

Usage:
  python nv_merge_csvs.py --indir downloads --outcsv statewide/SchoolRatings_MASTER_2023-24.csv --year 2024

Notes:
  - Adds 'district_name', 'district_id', and 'year' columns based on filename and/or a provided manifest.
  - If you pass --manifest out/download_manifest.json (from the downloader), the join will be exact.
"""
import argparse, os, re, json
from pathlib import Path
import pandas as pd

def load_manifest(manifest_path: Path):
  if manifest_path and manifest_path.exists():
    with manifest_path.open("r", encoding="utf-8") as f:
      return {Path(rec["csv_path"]).name: rec for rec in json.load(f)}
  return {}

def infer_from_filename(name: str):
  # Expected: SchoolRatings_<district_id>_<slug>.csv
  m = re.match(r"SchoolRatings_(\d+)_([^.]+)\.csv$", name)
  if m:
    return {"district_id": m.group(1), "district_name": m.group(2).replace("_", " ")}
  return {"district_id": None, "district_name": None}

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--indir", type=str, default="downloads")
  ap.add_argument("--outcsv", type=str, default="statewide/SchoolRatings_MASTER_2023-24.csv")
  ap.add_argument("--manifest", type=str, default="out/download_manifest.json")
  ap.add_argument("--year", type=int, default=2024)
  args = ap.parse_args()

  indir = Path(args.indir)
  files = sorted([p for p in indir.glob("*.csv") if p.name.lower().startswith("schoolratings")])
  if not files:
    print(f"No SchoolRatings*.csv files found in {indir}")
    return

  manifest = load_manifest(Path(args.manifest))
  rows = []
  for f in files:
    df = pd.read_csv(f)
    meta = manifest.get(f.name, {})
    if not meta:
      meta = infer_from_filename(f.name)
    df["district_id"] = meta.get("district_id")
    df["district_name"] = meta.get("district_name")
    df["year"] = args.year
    rows.append(df)

  combined = pd.concat(rows, ignore_index=True)
  outcsv = Path(args.outcsv); outcsv.parent.mkdir(parents=True, exist_ok=True)
  combined.to_csv(outcsv, index=False)
  # Also write Excel for convenience
  outexcel = outcsv.with_suffix(".xlsx")
  combined.to_excel(outexcel, index=False)
  print(f"Wrote {outcsv} and {outexcel}. Rows: {combined.shape[0]}  Cols: {combined.shape[1]}")

if __name__ == "__main__":
  main()
