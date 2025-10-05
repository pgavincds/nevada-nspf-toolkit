#!/usr/bin/env python3
import argparse, csv, hashlib, json, re
from datetime import datetime
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def year_label(y: int) -> str:
    return f"{y-1}-{str(y%100).zfill(2)}"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def csv_shape(path: Path):
    try:
        df = pd.read_csv(path, dtype=str)
        return len(df), len(df.columns)
    except Exception:
        return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True, help="Column year, e.g. 2025 for 2024–25")
    args = ap.parse_args()

    label = year_label(args.year)
    out_csv = ROOT / f"data/manifests/{label}_manifest.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    # District ids → names
    ids_json = ROOT / "out/district_ids.json"
    idmap = {}
    if ids_json.exists():
        arr = json.load(open(ids_json, "r", encoding="utf-8"))
        idmap = { str(d["district_id"]): d.get("district_name") for d in arr }

    rows = []

    # 1) Ratings/NSPF district CSV downloads
    dl_dir = ROOT / f"downloads/{args.year}"
    if dl_dir.exists():
        for fp in sorted(dl_dir.glob("*.csv")):
            m = re.match(r"SchoolRatings_(?P<label>[\d\-]+)_(?P<did>\d+)_.+\.csv$", fp.name)
            did = m.group("did") if m else None
            dname = idmap.get(did)
            url = f"https://nevadareportcard.nv.gov/DI/nspf/{did}/{args.year}/statedistrict" if did else None
            nrows, ncols = csv_shape(fp)
            rows.append({
                "dataset": "ratings_by_district",
                "year_label": label,
                "path": str(fp.relative_to(ROOT)),
                "source_url": url,
                "sha256": sha256(fp),
                "bytes": fp.stat().st_size,
                "rows": nrows,
                "cols": ncols,
                "district_id": did,
                "district_name": dname,
                "note": "District School Ratings CSV"
            })

    # 2) Statewide master (merged)
    master_csv = ROOT / f"statewide/SchoolRatings_MASTER_{label}.csv"
    if master_csv.exists():
        nrows, ncols = csv_shape(master_csv)
        rows.append({
            "dataset": "statewide_master",
            "year_label": label,
            "path": str(master_csv.relative_to(ROOT)),
            "source_url": "compiled from district CSVs",
            "sha256": sha256(master_csv),
            "bytes": master_csv.stat().st_size,
            "rows": nrows,
            "cols": ncols,
            "district_id": None,
            "district_name": None,
            "note": "Merged output"
        })

    # 3) Enrollment (xlsx + preview csv)
    enroll_xlsx = ROOT / f"data/enrollment/{label}.xlsx"
    if enroll_xlsx.exists():
        rows.append({
            "dataset": "enrollment_xlsx",
            "year_label": label,
            "path": str(enroll_xlsx.relative_to(ROOT)),
            "source_url": f"https://webapp-strapi-paas-prod-nde-001.azurewebsites.net/uploads/{label.replace('-','_')}_school_year_validation_day_student_counts",
            "sha256": sha256(enroll_xlsx),
            "bytes": enroll_xlsx.stat().st_size,
            "rows": None,
            "cols": None,
            "district_id": None,
            "district_name": None,
            "note": "Validation Day counts (xlsx)"
        })
    enroll_preview = ROOT / f"data/enrollment/{label}_preview.csv"
    if enroll_preview.exists():
        nrows, ncols = csv_shape(enroll_preview)
        rows.append({
            "dataset": "enrollment_preview",
            "year_label": label,
            "path": str(enroll_preview.relative_to(ROOT)),
            "source_url": "derived from enrollment xlsx (School Level Totals)",
            "sha256": sha256(enroll_preview),
            "bytes": enroll_preview.stat().st_size,
            "rows": nrows,
            "cols": ncols,
            "district_id": None,
            "district_name": None,
            "note": "Flat preview CSV"
        })

    # 4) Disaggregated ZIP + extracted files (if present)
    disagg_zip = ROOT / f"data/nspf-disagg/{label}.zip"
    if disagg_zip.exists():
        rows.append({
            "dataset": "nspf_disagg_zip",
            "year_label": label,
            "path": str(disagg_zip.relative_to(ROOT)),
            "source_url": "https://nevadareportcard.nv.gov/DI/MoreDownload?filename=NSPF%20Disaggregated%20Data%20File.zip",
            "sha256": sha256(disagg_zip),
            "bytes": disagg_zip.stat().st_size,
            "rows": None,
            "cols": None,
            "district_id": None,
            "district_name": None,
            "note": "As published"
        })
    disagg_dir = ROOT / f"data/nspf-disagg/{label}"
    if disagg_dir.exists():
        for fp in sorted(disagg_dir.rglob("*")):
            if fp.is_file():
                nrows = ncols = None
                if fp.suffix.lower() == ".csv":
                    nrows, ncols = csv_shape(fp)
                rows.append({
                    "dataset": "nspf_disagg_file",
                    "year_label": label,
                    "path": str(fp.relative_to(ROOT)),
                    "source_url": "unzipped from disagg zip",
                    "sha256": sha256(fp),
                    "bytes": fp.stat().st_size,
                    "rows": nrows,
                    "cols": ncols,
                    "district_id": None,
                    "district_name": None,
                    "note": fp.suffix.lower().lstrip(".")
                })

    # Write manifest
    cols = ["dataset","year_label","path","source_url","sha256","bytes","rows","cols","district_id","district_name","note"]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"Wrote {out_csv}  ({len(rows)} entries)")
