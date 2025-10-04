#!/usr/bin/env python3
"""
Automate CSV downloads of NSPF School Rating Report for each district (LEA).

Approach:
  - Navigate to the portal's profile page.
  - Use the same in-page function call DataPortal.Nav.ToNSPFStateDistrict(<id>, <year>)
    to open the district-level School Rating Report.
  - Click the "CSV Download" link.
  - Save the CSV as downloads/SchoolRatings_<district_id>_<slugified_name>.csv

Usage:
  python nv_download_nspf_by_district.py --ids out/district_ids.json --year 2024 --outdir downloads

Requires:
  pip install playwright
  playwright install
"""
import asyncio, json, argparse, re, os, sys, unicodedata
from pathlib import Path
from typing import List, Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

PROFILE_URL = "https://nevadareportcard.nv.gov/DI/main/profile"

def slugify(value: str) -> str:
  value = str(value)
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub(r'[^a-zA-Z0-9]+', '_', value).strip('_')
  return value.lower() or "district"

async def download_for_district(page, district_id: str, year: int, outdir: Path, district_name: str):
  # Navigate via the site-provided function so we land on the correct DI report
  await page.goto(PROFILE_URL, wait_until="domcontentloaded")
  await page.wait_for_timeout(1000)
  await page.evaluate(f"DataPortal && DataPortal.Nav && DataPortal.Nav.ToNSPFStateDistrict && DataPortal.Nav.ToNSPFStateDistrict({district_id}, {year});")
  # Wait for the DI page to render and expose the CSV link
  # First try a direct "CSV Download" button
  # If that fails, open a "Download" menu and then click "CSV Download"
  # We wrap in expect_download to capture the file reliably.
  filename_stub = f"SchoolRatings_{district_id}_{slugify(district_name)}.csv"
  try:
    async with page.expect_download() as dl_info:
      # Try a few possible selectors
      for sel in [
        'text="CSV Download"',
        'role=link[name="/.*CSV Download.*/"]',
        'text="Download Report" >> nth=0'  # may open a menu, we'll click CSV next
      ]:
        try:
          await page.wait_for_selector(sel, timeout=4000)
          await page.click(sel)
          break
        except PlaywrightTimeoutError:
          continue
    download = await dl_info.value
  except PlaywrightTimeoutError:
    # Fallback: open the download menu then click CSV
    try:
      await page.get_by_text("Download").first.click(timeout=4000)
      async with page.expect_download() as dl_info2:
        await page.get_by_text("CSV Download").click(timeout=4000)
      download = await dl_info2.value
    except Exception as e:
      raise RuntimeError(f"Could not find CSV download for district_id={district_id} ({district_name})") from e

  save_path = outdir / filename_stub
  await download.save_as(save_path.as_posix())
  return save_path

async def main_async(args):
  outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
  with open(args.ids, "r", encoding="utf-8") as f:
    districts: List[Dict[str, Any]] = json.load(f)

  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    ctx = await browser.new_context(accept_downloads=True)
    page = await ctx.new_page()

    results = []
    for d in districts:
      did = d.get("district_id")
      name = d.get("district_name", f"district_{did}")
      try:
        path = await download_for_district(page, did, args.year, Path(args.outdir), name)
        results.append({"district_id": did, "district_name": name, "year": args.year, "csv_path": str(path)})
        print(f"Downloaded: {path}")
      except Exception as e:
        print(f"[WARN] {did} {name}: {e}", file=sys.stderr)
    await browser.close()

  # Write a manifest of downloads
  manifest = Path(args.manifest)
  manifest.parent.mkdir(parents=True, exist_ok=True)
  with manifest.open("w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
  print(f"Wrote manifest: {manifest}")

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--ids", type=str, required=True, help="Path to district_ids.json produced by nv_scrape_lea_ids_playwright.py")
  ap.add_argument("--year", type=int, default=2024, help="Accountability year (e.g., 2024 for SY 2023-24)")
  ap.add_argument("--outdir", type=str, default="downloads", help="Directory to save CSVs")
  ap.add_argument("--manifest", type=str, default="out/download_manifest.json", help="Where to save a JSON of downloaded files")
  args = ap.parse_args()
  asyncio.run(main_async(args))

if __name__ == "__main__":
  main()
