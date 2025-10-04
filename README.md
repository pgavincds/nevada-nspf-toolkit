# nevada-nspf-toolkit

Tools to download and merge Nevada Report Card (NSPF) **district school ratings** CSVs by *column year* into a single statewide file.  
This project is **unofficial** and not affiliated with the Nevada Department of Education.

## What this does
- Downloads per-district CSVs from public report-card endpoints for a chosen **column year** (e.g., `2024` → **2023–24** school year).
- Saves files in a **year-specific folder** with year-labeled filenames.
- Merges all district files into one statewide CSV (and optionally Excel).

## What this does **not** do
- It doesn’t bypass authentication, quotas, or rate limits.
- It doesn’t scrape hidden data; it only automates downloads of publicly available files.

## Requirements
- Python 3.9+
- `pandas` (see `requirements.txt`)
- Optional: `openpyxl` (for Excel output)

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

shell
Copy code

## Quick start
1) Prepare the district list:
mkdir -p out
cp examples/district_ids.json out/district_ids.json

markdown
Copy code

2) Download for **2023–24** (column year `2024`):
python bulk_download_yeared.py --year 2024

sql
Copy code

3) Merge to a statewide file (add `--excel` if you installed `openpyxl`):
python merge_yeared.py --year 2024 --excel

markdown
Copy code

**Outputs**
downloads/2024/SchoolRatings_2023-24_<district_id>_<district>.csv
statewide/SchoolRatings_MASTER_2023-24.csv
statewide/SchoolRatings_MASTER_2023-24.xlsx

sql
Copy code

> Mapping: `--year 2024` → **2023–24**; `--year 2023` → **2022–23**.

## Etiquette & reliability
- Requests are paced with a small delay; increase with `--sleep 1.0` if desired.
- The downloader uses `curl` with retries for robustness.
- If a district’s CSV is empty in a given year (e.g., not rated / suppressed), it’s skipped during merge.

## Troubleshooting
- SSL issues are avoided because downloads use `curl`.
- Empty CSVs are expected for some LEAs in some years.
- Run the same commands with another `--year` to pull other years; files won’t overwrite.

## Contributing & contact
Suggestions and issues are welcome.  
Contact: pgavin@charterdevelopmentstrategies.com

## License
MIT — see `LICENSE`.

## Downloads
- [Statewide SchoolRatings MASTER (2024–25 CSV)](data/2024-25/SchoolRatings_MASTER_2024-25.csv)
- [Statewide SchoolRatings MASTER (2023–24 CSV)](data/2023-24/SchoolRatings_MASTER_2023-24.csv)
- [Statewide SchoolRatings MASTER (2022–23 CSV)](data/2022-23/SchoolRatings_MASTER_2022-23.csv)
