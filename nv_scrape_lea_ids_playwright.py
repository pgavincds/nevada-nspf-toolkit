#!/usr/bin/env python3
"""
Scrape district (LEA) IDs from Nevada Accountability Portal by reading the same
javascript:DataPortal.Nav.ToNSPFStateDistrict(<id>, <year>) anchors you see in the UI.

Usage:
  python nv_scrape_lea_ids_playwright.py --year 2024 --out out/district_ids.json
  (CSV will be written alongside the JSON automatically.)

Requires:
  pip install playwright
  playwright install
"""
import asyncio, json, argparse, os
from pathlib import Path
from typing import List, Dict, Any
from playwright.async_api import async_playwright

PROFILE_URL = "https://nevadareportcard.nv.gov/DI/main/profile"

JS_SCRAPE = r"""
() => {
  // Find the anchors that call DataPortal.Nav.ToNSPFStateDistrict(id, year)
  const anchors = Array.from(document.querySelectorAll('a[href^="javascript:DataPortal.Nav.ToNSPFStateDistrict"]'));
  const out = anchors.map(a => {
    const m = a.getAttribute('href').match(/ToNSPFStateDistrict\((\d+),\s*(\d{4})\)/);
    return m ? {
      district_name: (a.textContent || "").trim() || "(link)",
      district_id: m[1],
      year: m[2]
    } : null;
  }).filter(Boolean);
  return out;
}
"""

async def scrape_ids(year: int) -> List[Dict[str, Any]]:
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    ctx = await browser.new_context()
    page = await ctx.new_page()
    # 1) Load the profile page that lists Districts & Schools
    await page.goto(PROFILE_URL, wait_until="domcontentloaded")
    # Give the app a moment to render client-side anchors
    await page.wait_for_timeout(2000)
    # Try up to 3 times to account for slow scripts
    all_rows = []
    for _ in range(3):
      rows = await page.evaluate(JS_SCRAPE)
      if rows:
        all_rows = rows
        break
      await page.wait_for_timeout(1500)
    await browser.close()
  # De-duplicate and coerce year
  dedup = {}
  for r in all_rows:
    key = (r["district_id"], r["district_name"])
    dedup[key] = {"district_id": r["district_id"], "district_name": r["district_name"], "year": str(year)}
  return list(dedup.values())

def save_outputs(rows: List[Dict[str, Any]], out_json: Path):
  out_json.parent.mkdir(parents=True, exist_ok=True)
  with out_json.open("w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

  # CSV alongside JSON
  try:
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(out_json.with_suffix(".csv"), index=False)
  except Exception as e:
    print("Note: pandas not installed; skipping CSV export.", e)

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--year", type=int, default=2024, help="Accountability year, e.g., 2024 for SY 2023-24")
  ap.add_argument("--out", type=str, default="out/district_ids.json", help="Output JSON path")
  args = ap.parse_args()

  rows = asyncio.run(scrape_ids(args.year))
  if not rows:
    print("No district anchors found. Try loading the page in a regular browser to confirm anchors are present.")
  save_outputs(rows, Path(args.out))
  print(f"Wrote {len(rows)} districts to {args.out} and {Path(args.out).with_suffix('.csv')}")

if __name__ == "__main__":
  main()
