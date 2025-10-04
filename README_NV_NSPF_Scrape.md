# Nevada Accountability Portal — NSPF School Ratings Automation

This toolkit helps you:
1. **Scrape district (LEA) IDs** that power `DataPortal.Nav.ToNSPFStateDistrict(<id>, <year>)`.
2. **Auto-download** each district’s **School Ratings (NSPF)** CSV for SY **2023–24** (year `2024`).
3. **Merge** all those CSVs into one **statewide master** file.

> Tested with Python 3.10+ and macOS (Apple Silicon).

---

## Quick Start

```bash
# 1) Create a venv (recommended)
python3 -m venv .venv && source .venv/bin/activate

# 2) Install deps + browser
pip install -r requirements.txt
python -m playwright install

# 3) Scrape district IDs (outputs JSON + CSV in ./out/)
python nv_scrape_lea_ids_playwright.py --year 2024 --out out/district_ids.json

# 4) Download School Ratings CSVs for each district (to ./downloads)
python nv_download_nspf_by_district.py --ids out/district_ids.json --year 2024 --outdir downloads

# 5) Merge into one master file (CSV + Excel)
python nv_merge_csvs.py --indir downloads --outcsv statewide/SchoolRatings_MASTER_2023-24.csv --year 2024
```

---

## Notes & Tips

- The scraper reads the same `javascript:` anchors you shared (e.g., `javascript:DataPortal.Nav.ToNSPFStateDistrict(64843,2024);`), so it stays consistent with the site.
- The downloader calls that function **per district**, waits for the page to render, then clicks **CSV Download** and saves the file to `downloads/`.
- The merger adds `district_id`, `district_name`, and `year` columns so you can trace provenance.

### Troubleshooting
- **No anchors found in step 3**: Re-run the command — sometimes the app needs an extra second to render client-side content. You can also try without headless mode by modifying the launch call in the script (set `headless=False`) to watch it.
- **CSV link not found**: The downloader tries a few selectors (direct "CSV Download", then "Download" → "CSV Download"). If the portal UI changes, update the selectors near the top of `download_for_district()`.

---

## What you get
- `out/district_ids.json` & `.csv` — the LEA list for 2024.
- `downloads/SchoolRatings_<district_id>_<name>.csv` — raw per-LEA files.
- `statewide/SchoolRatings_MASTER_2023-24.csv` & `.xlsx` — one tidy statewide file.
