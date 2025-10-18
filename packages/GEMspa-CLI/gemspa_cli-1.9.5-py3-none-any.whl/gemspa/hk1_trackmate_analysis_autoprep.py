#!/usr/bin/env python3
# hk1_trackmate_analysis.py  (now TrackMate-aware intake)
import argparse, os
import pandas as pd
from pathlib import Path

# Use the shared prep utilities to accept a directory or TrackMate CSV
try:
    from gemspa.trackmate_prep import find_trackmate_spots_csv, clean_trackmate_csv
except Exception:
    # Allow running as a loose script if package not installed
    from gemspa.trackmate_prep import find_trackmate_spots_csv, clean_trackmate_csv  # type: ignore

# Reuse your earlier analysis class if present; else implement a tiny fallback
try:
    from hk1_trackmate_analysis import trajectory_analysis as HKTA   # self-import if defined that way
except Exception:
    HKTA = None

def run_hk1(inputs, outdir, px, dt, lag, minlen):
    os.makedirs(outdir, exist_ok=True)
    cleaned = []
    for inp in inputs:
        pick = find_trackmate_spots_csv(inp) or inp
        df = clean_trackmate_csv(pick)  # preserves extra columns
        out_csv = os.path.join(outdir, Path(pick).stem + "_clean.csv")
        df.to_csv(out_csv, index=False)
        cleaned.append(out_csv)

    # If a dedicated HK1 analysis class/script exists, this is where you'd call it on 'cleaned'.
    # For now we just confirm the cleaned files are ready.
    print("[HK1] cleaned files written:", cleaned)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="CSV(s) or folder(s) with TrackMate exports")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--px", type=float, default=0.1)
    ap.add_argument("--dt", type=float, default=0.05)
    ap.add_argument("--lag", type=int, default=1)
    ap.add_argument("--minlen", type=int, default=5)
    args = ap.parse_args()
    run_hk1(args.inputs, args.outdir, args.px, args.dt, args.lag, args.minlen)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
