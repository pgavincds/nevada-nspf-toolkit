#!/usr/bin/env python3
"""
Clean NSPF downloader – uses page.expect_download(), not context.expect_download.
Headless by default. Replace BASE_URL and SELECTOR_PATTERNS to match your site.
"""

from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ===== CONFIG: EDIT THESE FOR YOUR SITE =====
BASE_URL = "https://example.com/nspf"  # TODO: set the real page URL
SELECTOR_PATTERNS: List[str] = [
    '[data-district-id="{id}"][data-year="{year}"]',      # example
    'role=button[name="Download {year} – {name}"]',       # example
    'text="{name}"',                                      # fallback
]
CLICK_TIMEOUT_MS = 15_000
DOWNLOAD_TIMEOUT_MS = 60_000
RETRIES = 3
# ===== END CONFIG =====

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reliable NSPF downloader")
    p.add_argument("--ids", required=True, help="Path to JSON with district ids/names")
    p.add_argument("--year", required=True, type=int, help="Year like 2024")
    p.add_argument("--outdir", default="downloads", help="Download folder")
    p.add_argument("--headful", action="store_true", help="Show browser UI")
    return p.parse_args()

def load_ids(path: str):
    data = json.loads(Path(path).read_text())
    out = []
    def extract(item):
        # Accept both {id,name} and {district_id,district_name}, ints/strings too
        if isinstance(item, dict):
            idv = str(item.get("id", item.get("district_id",""))).strip()
            name = str(item.get("name", item.get("district_name", idv))).strip()
            if not idv:
                raise ValueError(f"Missing id in {item}")
            return idv, (name or idv)
        elif isinstance(item, (int, str)):
            return str(item), str(item)
        else:
            raise TypeError(f"Unsupported list item type: {type(item)}")

    if isinstance(data, list):
        for item in data:
            out.append(extract(item))
    elif isinstance(data, dict):
        for k, v in data.items():
            out.append((str(k), str(v)))
    else:
        raise TypeError(f"Unsupported ids JSON type: {type(data)}")
    return out


def slug(s: str) -> str:
    keep = []
    for ch in s.strip():
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        elif ch.isspace():
            keep.append("_")
    return ("".join(keep) or "unnamed")[:100]

def first_present_selector(page, idv: str, name: str, year: int) -> Optional[str]:
    for pat in SELECTOR_PATTERNS:
        sel = pat.format(id=idv, name=name, year=year)
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                return sel
        except Exception:
            pass
        try:
            page.locator(sel).first.wait_for(state="visible", timeout=1000)
            return sel
        except Exception:
            continue
    return None

def download_one(page, outdir: Path, idv: str, name: str, year: int) -> Dict[str, Any]:
    attempt, last_err = 0, None
    while attempt < RETRIES:
        attempt += 1
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=CLICK_TIMEOUT_MS)
            sel = first_present_selector(page, idv, name, year)
            if not sel:
                raise RuntimeError(f"No selector matched for id={idv}, name={name}, year={year}")
            with page.expect_download(timeout=DOWNLOAD_TIMEOUT_MS) as dl_info:
                page.locator(sel).first.click(timeout=CLICK_TIMEOUT_MS)
            download = dl_info.value
            suggested = download.suggested_filename or "file"
            ext = Path(suggested).suffix or ""
            fname = f"{idv}_{slug(name)}_{year}{ext}"
            target = outdir / fname
            download.save_as(target)
            return {
                "district_id": idv,
                "district_name": name,
                "year": year,
                "status": "ok",
                "filename": str(target),
                "suggested_filename": suggested,
                "attempts": attempt,
            }
        except PWTimeout as e:
            last_err = f"timeout: {e}"
        except Exception as e:
            last_err = str(e)
        time.sleep(1.2)
    return {
        "district_id": idv,
        "district_name": name,
        "year": year,
        "status": "error",
        "error": last_err or "unknown",
        "attempts": attempt,
    }

def main():
    args = parse_args()
    ids = load_ids(args.ids)
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    Path("out").mkdir(exist_ok=True)
    manifest: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        for idv, name in ids:
            row = download_one(page, outdir, idv, name, args.year)
            print(f"[{row['status'].upper()}] {idv} {name} -> {row.get('filename', row.get('error'))}")
            manifest.append(row)

        context.close()
        browser.close()

    mpath = Path("out/download_manifest.json")
    mpath.write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote manifest: {mpath}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
