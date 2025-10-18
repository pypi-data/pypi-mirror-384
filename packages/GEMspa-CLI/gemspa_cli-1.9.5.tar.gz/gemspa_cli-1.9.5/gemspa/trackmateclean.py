#!/usr/bin/env python3
"""
Packaged TrackMate cleaner for GEMspa.

- Recursively finds 'Spots in track(s) statistics.csv'
- Cleans to GEMspa schema (x,y,frame,track_id numeric; extras preserved)
- Standardizes names. Pools days by default (Traj_<COND>_<REP>.csv).
  Use include_date=True to write Traj_<COND>-<DATE>_<REP>.csv.
- Fixes multiple legacy Traj_* variants.

This module exposes:
    run_clean(root, out_dir=None, include_date=False, date_format='YYMMDD', move=False, dry_run=False)
    main()  # argparse entrypoint
"""
from __future__ import annotations
import argparse, re, shutil
from pathlib import Path
from typing import Optional, Dict
import pandas as pd
import numpy as np

ALLOWED_CONDITIONS = {"HK1", "HK1WT", "HK112V", "HK1180S", "HRAS", "vector"}

SPOTS_PATTERNS = [
    re.compile(r"^.*spots\s+in\s+tracks?\s+statistics\.csv$", re.I),
    re.compile(r"^.*spots\s+in\s+track\s+statistics\.csv$", re.I),
]

OLD_TRAJ_PATTERNS = [
    re.compile(r"^Traj_(?P<cond>[A-Za-z0-9]+)_(?P<rep>\d+)_(?P<date>\d{6,8})\.csv$", re.I),
    re.compile(r"^Traj_(?P<cond>[A-Za-z0-9]+)-(?P<date>\d{6,8})_(?P<rep>\d+)\.csv$", re.I),
    re.compile(r"^Traj_UNKNOWN-(?P<date>\d{6,8})_(?P<rep>\d+)\.csv$", re.I),
]

DATE_DIR_RE = re.compile(r"^(?P<yyyy>\d{4})(?P<mm>\d{2})(?P<dd>\d{2})$")
DATE_YYMMDD_RE = re.compile(r"(?<!\d)(\d{6})(?!\d)")
DATE_YYYYMMDD_RE = re.compile(r"(?<!\d)(\d{8})(?!\d)")
SPOOL_RE = re.compile(r"spool[_\-](\d+)", re.I)

def looks_like_spots_csv(name: str) -> bool:
    return any(pat.match(name) for pat in SPOTS_PATTERNS)

def find_datecode_from_ancestors(start_dir: Path, want_format: str = "YYMMDD") -> Optional[str]:
    for ancestor in [start_dir] + list(start_dir.parents):
        m = DATE_DIR_RE.match(ancestor.name)
        if m:
            yyyy, mm, dd = m.group("yyyy"), m.group("mm"), m.group("dd")
            return (yyyy + mm + dd) if want_format.upper() == "YYYYMMDD" else (yyyy[2:] + mm + dd)
        if re.fullmatch(r"\d{6}", ancestor.name):
            yy, mm, dd = ancestor.name[:2], ancestor.name[2:4], ancestor.name[4:]
            return (f"20{yy}{mm}{dd}") if want_format.upper() == "YYYYMMDD" else (yy + mm + dd)
    return None

def normalize_datecode(raw: Optional[str], name: str, want_format: str) -> Optional[str]:
    if raw:
        return raw
    m8 = DATE_YYYYMMDD_RE.search(name)
    if m8:
        yyyy, mm, dd = m8.group(1)[:4], m8.group(1)[4:6], m8.group(1)[6:]
        return (yyyy + mm + dd) if want_format.upper() == "YYYYMMDD" else (yyyy[2:] + mm + dd)
    m6 = DATE_YYMMDD_RE.search(name)
    if m6:
        yy, mm, dd = m6.group(1)[:2], m6.group(1)[2:4], m6.group(1)[4:]
        return (f"20{yy}{mm}{dd}") if want_format.upper() == "YYYYMMDD" else (yy + mm + dd)
    return None

def infer_condition_from_path(p: Path) -> Optional[str]:
    allowed_upper = {c.upper() for c in ALLOWED_CONDITIONS}
    # exact match up to 4 ancestors
    for anc in [p.parent, p.parent.parent, p.parent.parent.parent, p.parent.parent.parent.parent]:
        if not anc: break
        if anc.name.upper() in allowed_upper:
            return anc.name
    # substring fallback
    for anc in [p.parent, p.parent.parent, p.parent.parent.parent, p.parent.parent.parent.parent]:
        if not anc: break
        name_u = anc.name.upper()
        for cond in ALLOWED_CONDITIONS:
            if cond.upper() in name_u:
                return cond
    # filename fallback
    name = p.name
    if name.startswith("Traj_"):
        tail = name[5:].rsplit(".", 1)[0]
        return re.split(r"[-_]", tail, maxsplit=1)[0]
    m = re.match(r"^([A-Za-z0-9]+)[\-_]", name)
    if m:
        return m.group(1)
    return None

def infer_replicate_from_path_or_name(p: Path) -> Optional[int]:
    for anc in [p.parent, p.parent.parent, p.parent.parent.parent]:
        if not anc: break
        m = SPOOL_RE.search(anc.name)
        if m:
            return int(m.group(1))
    toks = re.split(r"[_\-]", p.stem)
    for tok in toks:
        if tok.isdigit():
            return int(tok)
    return None

def next_rep_index(counter: Dict[tuple, int], key: tuple) -> int:
    counter[key] = counter.get(key, 0) + 1
    return counter[key]

def clean_to_gemspa_schema(df: pd.DataFrame) -> pd.DataFrame:
    df = df.loc[:, ~df.columns.duplicated()].copy()
    cols = {c.lower(): c for c in df.columns}
    x_col  = cols.get("x") or cols.get("position_x")
    y_col  = cols.get("y") or cols.get("position_y")
    f_col  = cols.get("frame") or cols.get("spot_frame") or cols.get("t")
    tidcol = cols.get("track_id") or cols.get("track id") or cols.get("trajectory") or cols.get("trackindex")
    if x_col is None or y_col is None:
        raise ValueError("Could not find X/Y columns")
    if f_col is None:
        raise ValueError("Could not find frame/t column")
    if tidcol is None:
        raise ValueError("Could not find track_id/trajectory column")

    out = pd.DataFrame()
    out["x"] = pd.to_numeric(df[x_col], errors="coerce")
    out["y"] = pd.to_numeric(df[y_col], errors="coerce")
    out["frame"] = pd.to_numeric(df[f_col], errors="coerce")

    colobj = df[tidcol]
    if getattr(colobj, "ndim", 1) > 1:
        colobj = colobj.iloc[:, 0]
    out["track_id"] = pd.to_numeric(colobj, errors="coerce")

    out = out.dropna(subset=["x","y","frame","track_id"]).copy()
    out["frame"]    = out["frame"].astype("int64")
    out["track_id"] = out["track_id"].astype("int64")

    extras = df.loc[:, ~df.columns.isin([x_col, y_col, f_col, tidcol])]
    extras = extras.loc[:, ~extras.columns.duplicated()]
    out = pd.concat([out.reset_index(drop=True), extras.reset_index(drop=True)], axis=1)
    return out

def _fix_legacy_traj(p: Path, out_base: Optional[Path], include_date: bool, date_format: str, mover):
    for pat in OLD_TRAJ_PATTERNS:
        m = pat.match(p.name)
        if not m:
            continue
        cond = m.groupdict().get("cond") or infer_condition_from_path(p) or "UNKNOWN"
        rep  = int(m.groupdict().get("rep") or (infer_replicate_from_path_or_name(p) or 1))
        date = m.groupdict().get("date")
        if date:
            if len(date) == 8 and date_format.upper() == "YYMMDD":
                date = date[2:]
            if len(date) == 6 and date_format.upper() == "YYYYMMDD":
                date = "20" + date
        if include_date and date:
            newname = f"Traj_{cond}-{date}_{rep}.csv"
        else:
            newname = f"Traj_{cond}_{rep}.csv"
        dest_dir = out_base if out_base else p.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        dst = dest_dir / newname
        bump = 0
        while dst.exists():
            bump += 1
            if include_date and date:
                dst = dest_dir / f"Traj_{cond}-{date}_{rep + bump}.csv"
            else:
                dst = dest_dir / f"Traj_{cond}_{rep + bump}.csv"
        mover(str(p), str(dst))
        return True
    return False

def run_clean(root: str, out_dir: Optional[str] = None, include_date: bool = False,
              date_format: str = "YYMMDD", move: bool = False, dry_run: bool = False):
    root_p = Path(root).resolve()
    if not root_p.exists():
        raise SystemExit(f"[clean-trackmate] Root not found: {root}")

    out_base = Path(out_dir).resolve() if out_dir else None
    if out_base:
        out_base.mkdir(parents=True, exist_ok=True)

    mover = shutil.move if move else shutil.copy2
    rep_counter: Dict[tuple, int] = {}

    # Fix legacy Traj_* anywhere
    for p in root_p.rglob("Traj_*.csv"):
        # in dry-run, just print intended action if fixable
        for pat in OLD_TRAJ_PATTERNS:
            if pat.match(p.name):
                if dry_run:
                    print(f"[fix] {p}")
                else:
                    _fix_legacy_traj(p, out_base, include_date, date_format, mover)
                break

    # Collect & clean TrackMate tables
    for p in root_p.rglob("*.csv"):
        if not looks_like_spots_csv(p.name):
            continue

        cond = infer_condition_from_path(p) or "UNKNOWN"
        date_raw = find_datecode_from_ancestors(p.parent, want_format=date_format)
        datecode = normalize_datecode(date_raw, p.name, date_format)  # may be None

        rep = infer_replicate_from_path_or_name(p)
        if rep is None:
            key = (cond, datecode or "NA")
            rep = next_rep_index(rep_counter, key)

        if include_date and datecode:
            out_name = f"Traj_{cond}-{datecode}_{rep}.csv"
        else:
            out_name = f"Traj_{cond}_{rep}.csv"

        dest_dir = out_base if out_base else p.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        dst = dest_dir / out_name

        bump = 0
        while dst.exists():
            bump += 1
            if include_date and datecode:
                dst = dest_dir / f"Traj_{cond}-{datecode}_{rep + bump}.csv"
            else:
                dst = dest_dir / f"Traj_{cond}_{rep + bump}.csv"

        try:
            df = pd.read_csv(p, sep=None, engine="python")
        except Exception as e:
            print(f"[error] read {p}: {e}")
            continue
        try:
            cleaned = clean_to_gemspa_schema(df)
        except Exception as e:
            print(f"[error] clean {p}: {e}")
            continue

        if dry_run:
            print(f"[write] {p} -> {dst} (rows={len(cleaned)})")
        else:
            cleaned.to_csv(dst, index=False)

def main():
    ap = argparse.ArgumentParser(description="Collect & clean TrackMate 'Spots in tracks statistics.csv' to GEMspa Traj_*.csv")
    ap.add_argument("root", help="Root directory to scan")
    ap.add_argument("--out-dir", default=None, help="Write all outputs here (flat). If omitted, write beside nearest date folder.")
    ap.add_argument("--include-date", action="store_true", help="Include date in output name: Traj_<COND>-<DATE>_<REP>.csv (default: no date)")
    ap.add_argument("--date-format", choices=["YYMMDD","YYYYMMDD"], default="YYMMDD", help="DATECODE format when using --include-date")
    ap.add_argument("--move", action="store_true", help="Move instead of copy when fixing legacy Traj_*")
    ap.add_argument("--dry-run", action="store_true", help="Print actions; do not write files")
    args = ap.parse_args()
    run_clean(args.root, args.out_dir, args.include_date, args.date_format, args.move, args.dry_run)
    print("Done.")

if __name__ == "__main__":
    main()
