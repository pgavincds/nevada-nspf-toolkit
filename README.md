# Nevada NSPF Toolkit

Utilities to fetch and merge Nevada School Performance Framework (NSPF) public data with year-aware filenames and reproducibility helpers (schema snapshots + manifest).

• Downloads each district’s “District School Ratings” CSV for a given column year (example: --year 2025 → label 2024–25).  
• Merges district CSVs into a statewide master (CSV and optional Excel).  
• Pulls Enrollment (Validation Day) workbook and emits a normalized school-level preview CSV.  
• Fetches NSPF Disaggregated ZIP.  
• Builds a crosswalk of district/school codes; keeps decimal school codes (e.g., 1301.2) used to denote ES/MS/HS bands within a campus.  
• Captures schema header snapshots and a year manifest (file sizes + SHA256) for auditability.

----------------------------------------------------------------

## Quick start

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    # optional helpers used by some scripts
    pip install openpyxl requests beautifulsoup4

----------------------------------------------------------------

## Pull & merge district ratings (example: 2024–25)

NSPF “column year” drives the label. For label 2024–25, pass --year 2025.

Download all district CSVs (polite pacing):

    python bulk_download_yeared.py --year 2025 --sleep 1.0

Merge to statewide (CSV; add --excel for .xlsx):

    python merge_yeared.py --year 2025 --excel

(Optional) stage copies under data/<label>:

    mkdir -p data/2024-25
    cp statewide/SchoolRatings_MASTER_2024-25.csv  data/2024-25/
    cp statewide/SchoolRatings_MASTER_2024-25.xlsx data/2024-25/ 2>/dev/null || true

----------------------------------------------------------------

## Enrollment (Validation Day) + preview (2024–25)

Download the official workbook (xlsx):

    python fetch_enrollment.py --year 2025
    # -> data/enrollment/2024-25.xlsx

Produce normalized preview with district/school codes retained:

    python make_enrollment_preview_2025.py
    # -> data/enrollment/2024-25_preview.csv

----------------------------------------------------------------

## NSPF Disaggregated ZIP (2024–25)

    python fetch_nspf_disagg.py --year 2025
    # -> data/nspf-disagg/2024-25.zip
    #    extracted files under data/nspf-disagg/2024-25/

----------------------------------------------------------------

## Crosswalk (codes & names; decimals preserved)

Build crosswalk from Ratings + Enrollment preview:

    python build_crosswalk_2025.py
    # -> statewide/crosswalk_ids_2024-25.csv

Fill missing district_id using district code/name mapping from Ratings:

    python fill_crosswalk_ids_by_dcode_2025.py
    # -> statewide/crosswalk_ids_2024-25_filled.csv

Crosswalk columns:
- district_code (numeric-like code seen in report files)
- district_id   (NSPF DI id, e.g., 64841 = Washoe)
- district_name
- school_code   (string; decimals kept like 1301.2)
- school_name

Why decimals? NSPF uses decimal suffixes to represent level bands (ES/MS/HS) within a campus. Keeping them verbatim preserves join fidelity across files.

----------------------------------------------------------------

## Join sanity check (optional)

    python check_join_keys_2025.py
    # Prints row counts, inferred key columns, and sample normalized keys.

----------------------------------------------------------------

## Reproducibility (schema snapshots + manifest)

Snapshot headers for the year (ratings master, enrollment preview, disagg listing):

    python tools/snapshot_headers.py --year 2025
    # -> schema/2024-25/ratings_master_headers.json
    # -> schema/2024-25/enrollment_preview_headers.json
    # -> schema/2024-25/disagg_file_list.json

Generate a per-year manifest with byte sizes and SHA256 hashes:

    python tools/gen_manifest.py --year 2025
    # -> data/manifests/manifest_2024-25.csv

Verify local files match the manifest (OK/BAD tally):

    python - <<'PY'
    import csv, hashlib, pathlib
    root = pathlib.Path(".")
    mf = root/"data/manifests/manifest_2024-25.csv"
    ok = bad = 0
    with mf.open() as f:
        for row in csv.DictReader(f):
            p = root/row["path"]
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            if h == row["sha256"]: ok += 1
            else: bad += 1
    print("OK:", ok, "BAD:", bad)
    PY

----------------------------------------------------------------

## Example: pandas join via crosswalk

    import pandas as pd

    # Ratings (statewide master)
    R = pd.read_csv("statewide/SchoolRatings_MASTER_2024-25.csv", dtype=str)
    R["district_code"] = R["District Code"].str.replace(r"[^\d]", "", regex=True)
    R["school_code"]   = R["NSPF School Code"].astype(str)  # keep decimals

    # Enrollment preview
    E = pd.read_csv("data/enrollment/2024-25_preview.csv", dtype=str)
    E["district_code"] = E["Local Education Agency Code"].str.replace(r"[^\d]", "", regex=True)
    E["school_code"]   = E["School Code"].astype(str)

    # Crosswalk (filled)
    X = pd.read_csv("statewide/crosswalk_ids_2024-25_filled.csv", dtype=str)

    # Example join: enrich ratings with enrollment school names
    R2 = (R.merge(X[["district_code","school_code"]].drop_duplicates(),
                  on=["district_code","school_code"], how="left")
            .merge(E[["district_code","school_code","School Name"]],
                   on=["district_code","school_code"], how="left",
                   suffixes=("","_enroll")))

----------------------------------------------------------------

## What’s already in the repo (examples)

- data/2022-23/SchoolRatings_MASTER_2022-23.csv  
- data/2023-24/SchoolRatings_MASTER_2023-24.csv  
- data/2024-25/SchoolRatings_MASTER_2024-25.csv (+ .xlsx)  
- schema/2024-25/*.json (header snapshots)  
- data/manifests/manifest_2024-25.csv

----------------------------------------------------------------

## Notes & caveats

- Some LEAs/schools legitimately produce empty or suppressed CSVs in a given year (e.g., University LEA).
- Column names can shift year-to-year → rely on schema/<label>/ as year-specific truth.
- Disaggregated ZIP contents may change → treat fields as year-specific unless confirmed stable.
- Downloads use curl/requests with retries; please keep request rates polite (e.g., --sleep 1.0).

----------------------------------------------------------------

## Contributing & contact

Issues and PRs welcome—especially to extend crosswalks (e.g., NCES IDs) or add additional public pulls.  
Contact: pgavin@charterdevelopmentstrategies.com

License: MIT

(Last updated: 2025-10-05)
