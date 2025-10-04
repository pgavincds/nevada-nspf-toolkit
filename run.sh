#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install

python nv_scrape_lea_ids_playwright.py --year 2024 --out out/district_ids.json
python nv_download_nspf_by_district.py --ids out/district_ids.json --year 2024 --outdir downloads
python nv_merge_csvs.py --indir downloads --outcsv statewide/SchoolRatings_MASTER_2023-24.csv --year 2024

echo "Done. Check ./statewide for your master files."
