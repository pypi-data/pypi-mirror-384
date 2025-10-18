#!/usr/bin/env python3
"""
gemspa.trackmate_prep
---------------------
Utilities to standardize TrackMate exports for GEMspa.

Exports:
- find_trackmate_spots_csv(dir_or_csv) -> path
- clean_trackmate_csv(in_csv) -> pandas.DataFrame (canonical columns + ALL extras)
- standardize_to_traj(in_csv, out_dir, condition=None, date_code=None, rep=None) -> out_csv_path

Also works as a CLI:

    python -m gemspa.trackmate_prep <ROOT_DIR>

This walks <ROOT_DIR>, finds "Spots in tracks statistics.csv" (or similar),
writes cleaned copies into <ROOT_DIR>/raw as:
    Traj_<COND>-<DATE>_<REP>.csv
"""
import os, re, sys, glob
from pathlib import Path
from typing import Optional
import pandas as pd

PREFS = [
    "Spots in tracks statistics.csv",
    "spots in tracks statistics.csv",
    "All spots statistics.csv",
    "all spots statistics.csv",
]

def read_any(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=None, engine="python")

def find_trackmate_spots_csv(path: str) -> Optional[str]:
    p = Path(path)
    if p.is_file() and p.suffix.lower() == ".csv":
        return str(p)
    if p.is_dir():
        for name in PREFS:
            cand = p / name
            if cand.exists():
                return str(cand)
        # As a fallback, pick any CSV with plausible columns
        for cand in p.glob("*.csv"):
            try:
                df = read_any(str(cand))
            except Exception:
                continue
            low = [c.lower().strip() for c in df.columns]
            if any(c in low for c in ("position_x","x","x [µm]","x [um]")) and \
               any(c in low for c in ("position_y","y","y [µm]","y [um]")) and \
               any(c in low for c in ("frame","spot_frame")) and \
               any(c in low for c in ("track_id","track id","trajectory")):
                return str(cand)
    return None

def _col(df, *cands):
    low = {c.lower(): c for c in df.columns}
    for c in cands:
        if c in low: return low[c]
    return None

def clean_trackmate_csv(in_csv: str) -> pd.DataFrame:
    df = read_any(in_csv)
    # Strip whitespace
    df.columns = [str(c).strip() for c in df.columns]

    cx = _col(df, "position_x","x","x [µm]","x [um]","x (pixel)","x (µm)","x (um)")
    cy = _col(df, "position_y","y","y [µm]","y [um]","y (pixel)","y (µm)","y (um)")
    cf = _col(df, "frame","spot_frame","t","frame index","frame_index","frame id","frameid")
    ct = _col(df, "track_id","track id","trajectory","trackindex","track_index","id_track")

    if not all([cx,cy,cf,ct]):
        missing = [n for n,v in zip(["x","y","frame","track_id"],[cx,cy,cf,ct]) if v is None]
        raise RuntimeError(f"Missing required columns: {missing} in {in_csv}")

    out = df.copy()
    out["x"] = pd.to_numeric(out[cx], errors="coerce")
    out["y"] = pd.to_numeric(out[cy], errors="coerce")
    out["frame"] = pd.to_numeric(out[cf], errors="coerce")
    out["track_id"] = pd.to_numeric(out[ct], errors="coerce")
    out = out.dropna(subset=["x","y","frame","track_id"]).copy()
    out["track_id"] = out["track_id"].astype("int64")
    # Keep ALL other columns as-is
    return out

def _nearest_date_code(p: Path) -> str:
    for part in p.parts[::-1]:
        if re.fullmatch(r"\d{8}", part or ""):
            return part
    return "NA"

def _rep_from_name(stem: str) -> str:
    m = re.search(r"(\d+)", stem)
    return m.group(1) if m else "01"

def standardize_to_traj(in_csv: str, out_dir: str, condition: Optional[str]=None,
                        date_code: Optional[str]=None, rep: Optional[str]=None) -> str:
    in_path = Path(in_csv).resolve()
    out_base = Path(out_dir).resolve()
    out_base.mkdir(parents=True, exist_ok=True)

    # Infer defaults
    if condition is None:
        condition = in_path.parent.name  # folder name like 'HK1' or 'HK1-WT'
    if date_code is None:
        date_code = _nearest_date_code(in_path)
    if rep is None:
        rep = _rep_from_name(in_path.stem)

    clean = clean_trackmate_csv(str(in_path))
    clean["condition"] = condition

    out_csv = out_base / f"Traj_{condition}-{date_code}_{rep}.csv"
    clean.to_csv(out_csv, index=False)
    return str(out_csv)

def cli_walk_and_prep(root_dir: str) -> int:
    root = Path(root_dir).resolve()
    raw = root / "raw"
    raw.mkdir(exist_ok=True)
    count = 0

    # 0) Handle CSVs sitting directly in the root
    for cand in root.glob("*.csv"):
        try:
            out = standardize_to_traj(str(cand), str(raw))
            print("wrote", out)
            count += 1
        except Exception as e:
            print("[prep] skip", cand, "->", e)

    # 1) Walk subdirectories (existing behavior)
    for d in root.glob("**/*"):
        if not d.is_dir():
            continue
        spots = find_trackmate_spots_csv(str(d))
        if not spots:
            continue
        try:
            out = standardize_to_traj(spots, str(raw))
            print("wrote", out)
            count += 1
        except Exception as e:
            print("[prep] skip", d, "->", e)

    if count == 0:
        print("No TrackMate tables found under", root_dir)
    else:
        print(f"Converted {count} file(s). Raw CSVs at:", raw)
    return count


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m gemspa.trackmate_prep <ROOT_DIR>")
        sys.exit(2)
    cli_walk_and_prep(sys.argv[1])
