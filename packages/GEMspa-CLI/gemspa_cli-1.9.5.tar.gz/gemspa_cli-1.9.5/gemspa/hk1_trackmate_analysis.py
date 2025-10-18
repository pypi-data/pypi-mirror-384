#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HK1 advanced grouped analysis (TrackMate/GEMspa-compatible)

- Pools by condition across 1+ input folders.
- Uses the same filtering parameters as GEMspa core:
    * minlen                  (minimum frames per track)
    * lag                     (tlag_cutoff used for MSD calculation)
    * filter_D_min/max        (μm^2/s)
    * filter_alpha_min/max    (dimensionless)
- Outputs into: <work_dir>/grouped_advanced_analysis

Per-track metrics saved:
    track_id, condition, D_fit, alpha_fit, r2_fit, vacf_lag1, confinement_idx,
    hull_area_um2, tortuosity, n_frames

Figures:
    - Box/violin plots of D_fit and alpha_fit by condition
    - VACF distributions (hist + mean curve)
    - Convex-hull area vs tortuosity scatter (per condition and pooled)

NOTE: Coordinates in the input Traj_*.csv are in PIXELS; we scale by micron_per_px.
"""

from __future__ import annotations
import os, re, math, json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Iterable, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Try to use the package fitter for consistency with GEMspa
try:
    from .msd_diffusion import msd_diffusion
except Exception:
    # Fallback shim: crude log-log fit if package class can't be imported
    class msd_diffusion:  # type: ignore
        def __init__(self, save_dir="."):
            self.save_dir = save_dir
        def fit_msd(self, msd_vec: np.ndarray, dt: float):
            # Fit MSD ≈ 4 D τ^α  (log10)
            L = len(msd_vec)
            tau = (np.arange(1, L+1, dtype=float)) * dt
            m = np.isfinite(msd_vec) & (msd_vec > 0) & (tau > 0)
            if m.sum() < 3:
                return (np.nan, np.nan, 0.0)
            x = np.log10(tau[m]); y = np.log10(msd_vec[m])
            a, b = np.polyfit(x, y, 1)
            yhat = a * x + b
            ss_res = np.sum((y - yhat)**2); ss_tot = np.sum((y - y.mean())**2) + 1e-12
            r2 = 1.0 - ss_res / ss_tot
            D = (10.0**b) / 4.0
            alpha = float(a)
            return (float(D), float(alpha), float(r2))

# ------------------------- utils -------------------------

REQUIRED = ("track_id", "frame", "x", "y")
COND_WHITELIST = {"HK1","HK1WT","HK112V","HK1180S","HRAS","vector"}

def _find_traj_csvs(root: str) -> List[str]:
    p = Path(root)
    if p.is_file() and p.name.startswith("Traj_") and p.suffix.lower()==".csv":
        return [str(p)]
    out = []
    for f in p.rglob("Traj_*.csv"):
        out.append(str(f))
    return sorted(out)

def _infer_condition_from_name(fname: str) -> str:
    """
    Accepts both:
      Traj_<COND>_<REP>.csv       (pooled days)
      Traj_<COND>-<DATE>_<REP>.csv
    Returns upper token (preserving original case).
    """
    base = os.path.splitext(os.path.basename(fname))[0]
    if base.startswith("Traj_"):
        tail = base[5:]
        # split on '-' or '_' for the first token
        m = re.split(r"[-_]", tail, maxsplit=1)
        if m:
            token = m[0]
            # If token is in whitelist by substring (e.g., 'vector_cells'), map to canonical
            for c in COND_WHITELIST:
                if c.lower() in token.lower():
                    return c
            return token
    # fallback
    return "UNKNOWN"

def _read_and_validate(traj_csv: str) -> pd.DataFrame:
    """
    Robustly load a TrackMate/GEMspa trajectory CSV and normalize column names.
    Accepts common aliases like POSITION_X/POSITION_Y/Spot frame/Trajectory/etc.
    Enforces numeric types and returns rows sorted by (track_id, frame).
    """
    # be flexible on delimiter and engine
    try:
        df = pd.read_csv(traj_csv, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(traj_csv)

    # --- Normalize headers (case-insensitive, alias-aware) ---
    lower_to_actual = {c.lower(): c for c in df.columns}

    def first_present(*opts):
        # opts are lowercase search keys
        for key in opts:
            if key in lower_to_actual:
                return lower_to_actual[key]
        return None

    src_track = first_present(
        "track_id", "trajectory", "track id", "trackid", "track", "trackindex"
    )
    src_x = first_present(
        "x", "position_x", "pos_x", "x (px)", "x_px", "x[px]", "x coordinate"
    )
    src_y = first_present(
        "y", "position_y", "pos_y", "y (px)", "y_px", "y[px]", "y coordinate"
    )
    src_frame = first_present(
        "frame", "spot_frame", "t", "time", "frame_id", "frame index", "frameindex"
    )

    rename_map = {}
    if src_track and src_track != "track_id":
        rename_map[src_track] = "track_id"
    if src_x and src_x != "x":
        rename_map[src_x] = "x"
    if src_y and src_y != "y":
        rename_map[src_y] = "y"
    if src_frame and src_frame != "frame":
        rename_map[src_frame] = "frame"

    if rename_map:
        df = df.rename(columns=rename_map)

    required = {"track_id", "x", "y", "frame"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"{traj_csv}: missing required column(s) {sorted(missing)}")
    
    # --- Enforce numeric schema & clean rows ---
    for col in ("x", "y", "frame", "track_id"):
        df[col] = pd.to_numeric(df[col], errors="coerce")   # <-- fix 'coerce' typo

    df = df.dropna(subset=["x", "y", "frame", "track_id"]).copy()
    df["frame"] = df["frame"].astype("int64")
    df["track_id"] = df["track_id"].astype("int64")

    return df.sort_values(["track_id", "frame"]).reset_index(drop=True)

def _msd_from_track(px_xy: np.ndarray, max_lag: int) -> np.ndarray:
    """Unbiased MSD for lags 1..max_lag (in *microns*)."""
    n = px_xy.shape[0]
    L = max_lag
    out = np.zeros(L, dtype=float)
    for k in range(1, L+1):
        dif = px_xy[k:] - px_xy[:-k]
        out[k-1] = (dif[:,0]**2 + dif[:,1]**2).mean() if len(dif) else np.nan
    return out

def _velocities(px_xy_um: np.ndarray, dt: float) -> np.ndarray:
    v = np.diff(px_xy_um, axis=0) / max(dt, 1e-12)
    return v

def _vacf(v: np.ndarray, max_lag: int) -> np.ndarray:
    """velocity autocorrelation for lags 0..max_lag (2D dot)."""
    n = v.shape[0]
    max_lag = min(max_lag, n-1) if n>1 else 0
    ac = np.zeros(max_lag+1, dtype=float)
    if n <= 1:
        return ac
    v0 = v - v.mean(axis=0, keepdims=True)
    denom = (v0*v0).sum(axis=1).mean() + 1e-12
    ac[0] = 1.0
    for k in range(1, max_lag+1):
        dots = (v0[:-k]*v0[k:]).sum(axis=1)
        ac[k] = dots.mean()/denom
    return ac

def _radius_of_gyration(px_xy_um: np.ndarray) -> float:
    c = px_xy_um.mean(axis=0)
    dif = px_xy_um - c
    return math.sqrt(((dif**2).sum(axis=1).mean()))

def _convex_hull_area(px_xy_um: np.ndarray) -> float:
    # Andrew's monotone chain in 2D
    pts = px_xy_um.astype(float)
    if len(pts) < 3:
        return 0.0
    pts = pts[np.lexsort((pts[:,1], pts[:,0]))]
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = np.array(lower[:-1] + upper[:-1])
    # polygon area (shoelace)
    x = hull[:,0]; y = hull[:,1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

def _tortuosity(px_xy_um: np.ndarray) -> float:
    seg = np.sqrt(((np.diff(px_xy_um,axis=0))**2).sum(axis=1))
    L = seg.sum()
    disp = np.linalg.norm(px_xy_um[-1] - px_xy_um[0])
    return float(L / max(disp, 1e-12))

def _condition_key_from_file(f: str) -> str:
    return _infer_condition_from_name(f)

# ------------------------- core -------------------------

def run_hk1(
    inputs: List[str],
    outdir: str,
    px: float,
    dt: float,
    lag: int,
    minlen: int,
    filter_D_min: Optional[float] = None,
    filter_D_max: Optional[float] = None,
    filter_alpha_min: Optional[float] = None,
    filter_alpha_max: Optional[float] = None,
) -> None:
    """
    Entrypoint used by gemspa-cli.

    Parameters mirror GEMspa CLI so users set filters *once*:
      px (micron_per_px), dt (time_step), lag (tlag_cutoff), minlen,
      filter_D_* and filter_alpha_*.
    """
    Path(outdir).mkdir(parents=True, exist_ok=True)
    fig_dir = Path(outdir) / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    msd_proc = msd_diffusion(save_dir=outdir)

    # Collect files
    files: List[str] = []
    for root in inputs:
        files.extend(_find_traj_csvs(root))
    if not files:
        print("[HK1] No Traj_*.csv found in provided inputs; nothing to do.")
        return

    # Pool by condition
    per_condition_rows: Dict[str, List[dict]] = defaultdict(list)

    for f in files:
        cond = _condition_key_from_file(f)
        df = _read_and_validate(f)

        # group by track
        for tid, g in df.groupby("track_id", sort=False):
            if len(g) < max(2, int(minlen)):
                continue
            # pixel→μm
            xy_um = g[["x","y"]].to_numpy(dtype=float) * float(px)

            # Compute per-track MSD (lags 1..lag or up to length-1)
            L = min(int(lag), max(1, xy_um.shape[0]-1))
            if L < 1:
                continue
            msd_vec = _msd_from_track(xy_um, L)

            # Fit with same routine as GEMspa
            D_fit, alpha_fit, r2_fit = msd_proc.fit_msd(msd_vec, float(dt))

            # Apply GEMspa-like filters if specified
            if (filter_D_min is not None and not (D_fit >= filter_D_min)) or \
               (filter_D_max is not None and not (D_fit <= filter_D_max)) or \
               (filter_alpha_min is not None and not (alpha_fit >= filter_alpha_min)) or \
               (filter_alpha_max is not None and not (alpha_fit <= filter_alpha_max)):
                continue

            # Kinematics
            v = _velocities(xy_um, float(dt))
            vacf = _vacf(v, max_lag=min(25, max(1, len(v)-1)))  # cap at 25 lags for plots
            vacf_lag1 = float(vacf[1]) if vacf.size > 1 else np.nan

            # Geometry metrics
            rg = _radius_of_gyration(xy_um)
            max_disp = np.max(np.sqrt(((xy_um - xy_um[0])**2).sum(axis=1))) if len(xy_um)>0 else 0.0
            confinement_idx = float(rg / max(max_disp, 1e-12))
            hull_area = _convex_hull_area(xy_um)
            tort = _tortuosity(xy_um)

            per_condition_rows[cond].append({
                "track_id": int(tid),
                "condition": cond,
                "D_fit": float(D_fit),
                "alpha_fit": float(alpha_fit),
                "r2_fit": float(r2_fit),
                "vacf_lag1": vacf_lag1,
                "confinement_idx": confinement_idx,
                "hull_area_um2": float(hull_area),
                "tortuosity": float(tort),
                "n_frames": int(len(g)),
            })

    # Write per-condition CSVs + pooled CSV
    all_rows = []
    for cond, rows in per_condition_rows.items():
        if not rows:
            continue
        cdf = pd.DataFrame(rows)
        cdf.to_csv(Path(outdir) / f"{cond}_advanced_metrics.csv", index=False)
        all_rows.extend(rows)
    if not all_rows:
        print("[HK1] No tracks survived filters; no outputs.")
        return
    all_df = pd.DataFrame(all_rows)
    all_df.to_csv(Path(outdir) / "all_conditions_advanced_metrics.csv", index=False)

    # --------- Figures ---------
    def _box_or_violin(ax, data_by_cond: Dict[str, np.ndarray], title: str, ylabel: str, violin=True):
        keys = sorted(data_by_cond.keys())
        data = [data_by_cond[k] for k in keys]
        if violin:
            parts = ax.violinplot(data, showmeans=True, showextrema=False)
        else:
            ax.boxplot(data, notch=True, showfliers=False)
        ax.set_xticks(range(1,len(keys)+1)); ax.set_xticklabels(keys, rotation=30, ha="right")
        ax.set_title(title); ax.set_ylabel(ylabel)

    # D_fit by condition
    d_by = {c: all_df.query("condition == @c")["D_fit"].to_numpy() for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])}
    if d_by:
        fig, ax = plt.subplots(figsize=(8,5))
        _box_or_violin(ax, d_by, "Diffusion coefficient (D_fit)", "μm²/s", violin=True)
        fig.tight_layout(); fig.savefig(Path(fig_dir)/"D_fit_by_condition.png", dpi=300); plt.close(fig)

    # alpha by condition
    a_by = {c: all_df.query("condition == @c")["alpha_fit"].to_numpy() for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])}
    if a_by:
        fig, ax = plt.subplots(figsize=(8,5))
        _box_or_violin(ax, a_by, "Anomalous exponent (alpha_fit)", "α", violin=True)
        fig.tight_layout(); fig.savefig(Path(fig_dir)/"alpha_by_condition.png", dpi=300); plt.close(fig)

    # VACF lag-1 histogram per condition (grid)
    conds = [c for c in sorted(per_condition_rows.keys()) if len(per_condition_rows[c])]
    if conds:
        n = len(conds); ncols = min(3, n); nrows = math.ceil(n / ncols)
        fig, axs = plt.subplots(nrows, ncols, figsize=(4*ncols, 3.2*nrows), squeeze=False)
        for i,c in enumerate(conds):
            ax = axs[i//ncols, i % ncols]
            x = all_df.query("condition == @c")["vacf_lag1"].dropna().to_numpy()
            if len(x):
                ax.hist(x, bins=30, edgecolor="black")
            ax.set_title(f"{c}  (VACF lag-1)")
        fig.tight_layout(); fig.savefig(Path(fig_dir)/"VACF_lag1_hist_by_condition.png", dpi=300); plt.close(fig)

    # Hull area vs tortuosity scatter (pooled)
    fig, ax = plt.subplots(figsize=(7,5))
    for c in conds:
        sub = all_df.query("condition == @c")
        ax.scatter(sub["hull_area_um2"], sub["tortuosity"], label=c, alpha=0.6, s=18)
    ax.set_xlabel("Convex hull area (μm²)"); ax.set_ylabel("Tortuosity (L/disp)")
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(Path(fig_dir)/"hull_area_vs_tortuosity.png", dpi=300); plt.close(fig)

    # Save parameters used
    params = dict(
        micron_per_px=float(px),
        time_step=float(dt),
        tlag_cutoff=int(lag),
        min_track_len=int(minlen),
        filter_D_min=(None if filter_D_min is None else float(filter_D_min)),
        filter_D_max=(None if filter_D_max is None else float(filter_D_max)),
        filter_alpha_min=(None if filter_alpha_min is None else float(filter_alpha_min)),
        filter_alpha_max=(None if filter_alpha_max is None else float(filter_alpha_max)),
    )
    pd.Series(params).to_csv(Path(outdir)/"params_log.csv", header=False)
    with open(Path(outdir)/"params_log.json","w") as f:
        json.dump(params, f, indent=2)

    print(f"[HK1] Wrote advanced metrics to: {outdir}")
    print(f"[HK1] Figures → {fig_dir}")

# ------------------------- CLI shim (optional) -------------------------

def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="HK1 grouped advanced analysis")
    ap.add_argument("work_dir", help="Folder containing Traj_*.csv (can be many).")
    ap.add_argument("--outdir", default=None, help="Output directory (default: <work_dir>/grouped_advanced_analysis)")
    ap.add_argument("--px", type=float, required=True, help="micron per pixel")
    ap.add_argument("--dt", type=float, required=True, help="time step (s)")
    ap.add_argument("--lag", type=int, default=3, help="tlag cutoff for MSD")
    ap.add_argument("--minlen", type=int, default=3, help="minimum frames per track")
    ap.add_argument("--filter-D-min", type=float, default=None)
    ap.add_argument("--filter-D-max", type=float, default=None)
    ap.add_argument("--filter-alpha-min", type=float, default=None)
    ap.add_argument("--filter-alpha-max", type=float, default=None)
    args = ap.parse_args()

    outdir = args.outdir or os.path.join(args.work_dir, "grouped_advanced_analysis")
    run_hk1(
        inputs=[args.work_dir],
        outdir=outdir,
        px=args.px,
        dt=args.dt,
        lag=args.lag,
        minlen=args.minlen,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
    )

if __name__ == "__main__":
    _cli()
