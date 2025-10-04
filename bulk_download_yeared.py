#!/usr/bin/env python3
import json, re, subprocess, time, argparse
from pathlib import Path

def slug(s): return re.sub(r'[^a-z0-9]+','_', s.lower()).strip('_')
def acad_label(y: int) -> str:
    return f"{y-1}-{str(y)[-2:]}"  # 2024 -> "2023-24"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default="out/district_ids.json")
    ap.add_argument("--year", type=int, required=True, help="Column year (e.g., 2024 for 2023-24)")
    ap.add_argument("--outdir", default="downloads")
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    label = acad_label(args.year)
    outdir = Path(args.outdir) / str(args.year)
    outdir.mkdir(parents=True, exist_ok=True)

    ids = json.load(open(args.ids, 'r', encoding='utf-8'))
    ok = fail = 0
    for d in ids:
        did = str(d["district_id"])
        name = d.get("district_name", f"district_{did}")
        url = f"https://nevadareportcard.nv.gov/DI/nspf/{did}/{args.year}/statedistrict"
        fp = outdir / f"SchoolRatings_{label}_{did}_{slug(name)}.csv"
        print(f"Fetching {did} {name} -> {fp.name}")
        r = subprocess.run(["curl","-fsSL","--retry","3","--retry-delay","1", url, "-o", str(fp)])
        if r.returncode == 0 and fp.exists() and fp.stat().st_size > 0:
            print(f"  Saved ({fp.stat().st_size:,} bytes)")
            ok += 1
        else:
            print(f"  FAIL")
            fail += 1
        time.sleep(args.sleep)

    print(f"\nDone. OK={ok}, FAIL={fail}. Files in {outdir}")

if __name__ == "__main__":
    main()
