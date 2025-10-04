# nevada-nspf-toolkit
Year-aware scripts to download & merge Nevada Report Card (NSPF) district school ratings by column year.

## Quick start
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdir -p out && cp examples/district_ids.json out/district_ids.json
python bulk_download_yeared.py --year 2024
python merge_yeared.py --year 2024 --excel   # install openpyxl to enable Excel
