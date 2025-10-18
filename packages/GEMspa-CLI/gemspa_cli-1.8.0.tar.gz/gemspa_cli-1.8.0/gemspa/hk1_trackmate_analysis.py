#!/usr/bin/env python3
"""
HK1 analysis intake, pooling, per-track metrics, and summary plots.

Adds:
- VACF (normalized) per condition (mean across tracks)
- Confinement index distributions (CI = 1 - net_disp/total_path)
- Convex-hull area & perimeter per track (μm & μm²), plots & scatter vs tortuosity
- Tortuosity τ = total_path / net_displacement

Outputs under --outdir:
    cleaned/Traj_<COND>-<DATE>_<REP>_clean.csv
    pooled/Traj_<COND>_pooled.csv
    pooled_tracks/track_metrics_<COND>.csv
    pooled_msd/pooled_msd_<COND>.csv
    figures/<COND>_msd.png
    figures/<COND>_steps.png
    figures/<COND>_vanhove.png
    figures/<COND>_angles.png
    figures/<COND>_alpha2.png
    figures/<COND>_vacf.png
    figures/<COND>_confinement.png
    figures/<COND>_hull_area.png
    figures/<COND>_hull_vs_tortuosity.png
"""

from __future__ import annotations
import os, glob, argparse, re
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- configuration ----------------

TRAJ_GLOB = "Traj_*.csv"
ALLOWED_CONDITIONS = {"HK1", "HK1WT", "HK112V", "HK1180S", "HRAS", "vector"}
DEFAULT_MAX_LAG = 10           # for ensemble MSD / alpha2 / VACF
DEFAULT_BOOTSTRAP = 500        # bootstrap samples for MSD CI
MIN_TRACK_LEN_FOR_METRICS = 5  # frames (min per-track length to include in metrics)

# ---------------- filename parsing ----------------

_cond_re = re.compile(
    r"^Traj_(?P<cond>[^_\-]+[A-Za-z0-9]*)(?:[-_])(?P<date>\d{6,8})(?:[_-](?P<rep>\d+))?\.csv$",
    re.I,
)

def parse_condition_from_filename(path: str) -> Tuple[str, str | None, str | None]:
    name = Path(path).name
    m = _cond_re.match(name)
    if m:
        return m.group("cond"), m.group("date"), m.group("rep")
    # fallback
    if name.startswith("Traj_") and name.lower().endswith(".csv"):
        tail = name[5:-4]
        cond = tail.split("-")[0].split("_")[0]
        md = re.search(r"(\d{6,8})", tail)
        date = md.group(1) if md else None
        mr = re.search(r"_(\d+)(?:\D|$)", tail)
        rep  = mr.group(1) if mr else None
        return cond, date, rep
    return "UNKNOWN", None, None

# ---------------- intake & standardization ----------------

def _dedupe_and_standardize(df: pd.DataFrame) -> pd.DataFrame:
    """Return canonical table with numeric x,y,frame,track_id and all extra columns preserved."""
    # Drop duplicate column labels
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # Case-insensitive header map
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
    if hasattr(colobj, "ndim") and getattr(colobj, "ndim", 1) > 1:
        colobj = colobj.iloc[:, 0]
    out["track_id"] = pd.to_numeric(colobj, errors="coerce")

    out = out.dropna(subset=["x","y","frame","track_id"]).copy()
    out["frame"] = out["frame"].astype("int64")
    out["track_id"] = out["track_id"].astype("int64")

    # Preserve extra (non-duplicated) columns
    extras = df.loc[:, ~df.columns.isin([x_col, y_col, f_col, tidcol])]
    extras = extras.loc[:, ~extras.columns.duplicated()]
    out = pd.concat([out.reset_index(drop=True), extras.reset_index(drop=True)], axis=1)
    return out

def _iter_traj_csvs(inputs: List[str]) -> List[str]:
    files: List[str] = []
    for inp in inputs:
        p = Path(inp)
        if p.is_dir():
            files.extend(sorted(glob.glob(str(p / TRAJ_GLOB))))
        elif p.is_file() and p.name.startswith("Traj_") and p.suffix.lower() == ".csv":
            files.append(str(p))
    return sorted(set(files))

# ---------------- geometry / metrics helpers ----------------

def _steps_xy(df_sorted: pd.DataFrame) -> np.ndarray:
    dxy = df_sorted[["x","y"]].to_numpy()
    return np.sqrt(np.sum(np.diff(dxy, axis=0)**2, axis=1))  # Δr per frame (pixels)

def _msd_track(df_sorted: pd.DataFrame, px_um: float, max_lag: int) -> Tuple[np.ndarray, np.ndarray]:
    xy = df_sorted[["x","y"]].to_numpy() * px_um
    n = len(xy)
    L = min(max_lag, max(1, n-1))
    lags = np.arange(1, L+1)
    msd = np.empty(L, dtype=float)
    for i, lag in enumerate(lags, 1):
        d = xy[lag:] - xy[:-lag]
        msd[i-1] = np.nan if d.size == 0 else float(np.mean(np.sum(d**2, axis=1)))
    return lags, msd

def _fit_short_lag_powerlaw(lags: np.ndarray, msd: np.ndarray, dt: float, Lfit: int = 3) -> Tuple[float, float]:
    """Return (D_um2_s, alpha). Fit log(MSD) = log(4D) + alpha*log(tau) with tau=lags*dt."""
    L = min(Lfit, len(lags))
    if L < 2:
        return np.nan, np.nan
    tau = lags[:L] * dt
    y = np.log(np.maximum(msd[:L], 1e-30))
    X = np.vstack([np.ones(L), np.log(tau)]).T
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    c0, alpha = beta
    D = np.exp(c0) / 4.0
    return float(D), float(alpha)

def _alpha2_vs_lag(df_sorted: pd.DataFrame, px_um: float, max_lag: int) -> Tuple[np.ndarray, np.ndarray]:
    xy = df_sorted[["x","y"]].to_numpy() * px_um
    L = min(max_lag, max(1, len(xy)-1))
    lags = np.arange(1, L+1)
    alpha2 = np.full(L, np.nan, float)
    for i, lag in enumerate(lags, 1):
        d = xy[lag:] - xy[:-lag]
        if d.size == 0:
            continue
        r2 = np.sum(d**2, axis=1)
        r4 = r2**2
        m2 = np.mean(r2)
        m4 = np.mean(r4)
        if m2 > 0:
            alpha2[i-1] = m4 / (2*m2*m2) - 1.0  # 2D convention
    return lags, alpha2

# VACF helpers
def _velocities(df_sorted: pd.DataFrame, px_um: float, dt: float) -> np.ndarray:
    xy = df_sorted[["x","y"]].to_numpy() * px_um
    v = np.diff(xy, axis=0) / max(dt, 1e-12)  # (N-1, 2)
    return v

def _vacf_normalized(df_sorted: pd.DataFrame, px_um: float, dt: float, max_lag: int) -> Tuple[np.ndarray, np.ndarray]:
    v = _velocities(df_sorted, px_um, dt)
    if len(v) < 2:
        L = 1
        return np.arange(1, L+1), np.full(L, np.nan)
    L = min(max_lag, len(v)-1)
    lags = np.arange(1, L+1)
    v2 = np.sum(v*v, axis=1)
    denom = np.mean(v2) if np.mean(v2) > 0 else np.nan
    vacf = np.full(L, np.nan)
    for i, lag in enumerate(lags, 1):
        dot = np.sum(v[lag:] * v[:-lag], axis=1)
        vacf[i-1] = np.mean(dot) / denom if denom == denom else np.nan
    return lags, vacf

# Convex hull (Andrew's monotone chain) without external deps
def _convex_hull(points: np.ndarray) -> np.ndarray:
    pts = np.unique(points, axis=0)
    if len(pts) <= 1:
        return pts
    pts = pts[np.lexsort((pts[:,1], pts[:,0]))]  # sort by x, then y

    def cross(o, a, b):  # 2D cross product (OA x OB)
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(tuple(p))
    upper = []
    for p in pts[::-1]:
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(tuple(p))
    hull = np.array(lower[:-1] + upper[:-1], dtype=float)
    return hull

def _poly_area_perimeter(poly: np.ndarray) -> Tuple[float, float]:
    if poly is None or len(poly) < 3:
        return 0.0, 0.0
    x, y = poly[:,0], poly[:,1]
    area = 0.5 * np.abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    per = np.sum(np.sqrt(np.sum(np.diff(np.vstack([poly, poly[0]]), axis=0)**2, axis=1)))
    return float(area), float(per)

def _path_length_and_net_disp(df_sorted: pd.DataFrame, px_um: float) -> Tuple[float, float]:
    xy = df_sorted[["x","y"]].to_numpy() * px_um
    if len(xy) < 2:
        return 0.0, 0.0
    diffs = np.diff(xy, axis=0)
    total = float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))
    net = float(np.sqrt(np.sum((xy[-1]-xy[0])**2)))
    return total, net

# ---------------- plotting ----------------

def _ensure_figdir(figdir: str):
    os.makedirs(figdir, exist_ok=True)

def _bootstrap_mean(values: np.ndarray, n_boot: int = DEFAULT_BOOTSTRAP) -> Tuple[float, Tuple[float,float]]:
    rng = np.random.default_rng(0)
    if values.size == 0:
        return np.nan, (np.nan, np.nan)
    means = np.empty(n_boot, float)
    for i in range(n_boot):
        sample = rng.choice(values, size=values.size, replace=True)
        means[i] = np.nanmean(sample)
    means = np.sort(means)
    lo = means[int(0.025*n_boot)]
    hi = means[int(0.975*n_boot)]
    return float(np.mean(values)), (float(lo), float(hi))

def _plot_msd_condition(cond: str, lags: np.ndarray, msd_tracks: List[np.ndarray], out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    means, lo_ci, hi_ci = [], [], []
    for i in range(len(lags)):
        col = np.array([m[i] for m in msd_tracks if i < len(m)], dtype=float)
        m, (lo, hi) = _bootstrap_mean(col, n_boot=DEFAULT_BOOTSTRAP)
        means.append(m); lo_ci.append(lo); hi_ci.append(hi)
    means, lo_ci, hi_ci = np.array(means), np.array(lo_ci), np.array(hi_ci)
    plt.figure(figsize=(6,4))
    plt.plot(lags, means, lw=2)
    plt.fill_between(lags, lo_ci, hi_ci, alpha=0.25, linewidth=0)
    plt.xlabel("lag (frames)")
    plt.ylabel("MSD (μm²)")
    plt.title(f"{cond} — Ensemble MSD")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_steps_condition(cond: str, steps_um: np.ndarray, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    if steps_um.size == 0: return
    plt.figure(figsize=(6,4))
    counts, bins, _ = plt.hist(steps_um, bins=40, density=True, alpha=0.6)
    centers = 0.5*(bins[1:] + bins[:-1])
    kernel = np.ones(5)/5.0
    smooth = np.convolve(counts, kernel, mode="same")
    plt.plot(centers, smooth, lw=2)
    plt.xlabel("step length Δr (μm) at lag 1")
    plt.ylabel("PDF")
    plt.title(f"{cond} — Step-size distribution")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_vanhove_condition(cond: str, steps_um: np.ndarray, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    if steps_um.size == 0: return
    plt.figure(figsize=(6,4))
    counts, bins, _ = plt.hist(steps_um, bins=50, density=True, alpha=0.6)
    centers = 0.5*(bins[1:] + bins[:-1])
    plt.semilogy(centers, counts + 1e-12)
    plt.xlabel("|Δr| (μm) at lag 1")
    plt.ylabel("P(|Δr|)")
    plt.title(f"{cond} — van Hove (semi-log)")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_angles_condition(cond: str, df_sorted: pd.DataFrame, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    xy = df_sorted[["x","y"]].to_numpy()
    if len(xy) < 3: return
    v1 = xy[1:-1] - xy[0:-2]
    v2 = xy[2:]   - xy[1:-1]
    dot = np.sum(v1*v2, axis=1); n1 = np.linalg.norm(v1, axis=1); n2 = np.linalg.norm(v2, axis=1)
    cosang = np.clip(dot / (n1*n2 + 1e-12), -1.0, 1.0)
    ang = np.arccos(cosang)  # radians
    plt.figure(figsize=(6,4))
    plt.hist(ang, bins=36, density=True, alpha=0.8)
    plt.xlabel("turning angle (rad)")
    plt.ylabel("PDF")
    plt.title(f"{cond} — Turning angle histogram")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_alpha2_condition(cond: str, lags: np.ndarray, alpha2_tracks: List[np.ndarray], out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    means = []
    for i in range(len(lags)):
        col = np.array([a[i] for a in alpha2_tracks if i < len(a)], dtype=float)
        means.append(np.nanmean(col) if col.size else np.nan)
    means = np.array(means)
    plt.figure(figsize=(6,4))
    plt.plot(lags, means, lw=2)
    plt.axhline(0.0, ls="--", lw=1)
    plt.xlabel("lag (frames)")
    plt.ylabel("α₂ (non-Gaussian)")
    plt.title(f"{cond} — α₂ vs lag")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_vacf_condition(cond: str, lags: np.ndarray, vacf_tracks: List[np.ndarray], out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    means = []
    for i in range(len(lags)):
        col = np.array([a[i] for a in vacf_tracks if i < len(a)], dtype=float)
        means.append(np.nanmean(col) if col.size else np.nan)
    means = np.array(means)
    plt.figure(figsize=(6,4))
    plt.plot(lags, means, lw=2)
    plt.axhline(0.0, ls="--", lw=1)
    plt.xlabel("lag (frames)")
    plt.ylabel("VACF (normalized)")
    plt.title(f"{cond} — VACF")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_confinement_hist(cond: str, ci_values: np.ndarray, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    if ci_values.size == 0: return
    plt.figure(figsize=(6,4))
    plt.hist(ci_values, bins=40, density=True, alpha=0.8)
    plt.xlabel("Confinement index CI = 1 - net/total")
    plt.ylabel("PDF")
    plt.title(f"{cond} — Confinement index")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_hull_area_hist(cond: str, areas: np.ndarray, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    if areas.size == 0: return
    plt.figure(figsize=(6,4))
    plt.hist(areas, bins=40, density=True, alpha=0.8)
    plt.xlabel("Convex-hull area (μm²)")
    plt.ylabel("PDF")
    plt.title(f"{cond} — Hull area distribution")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

def _plot_hull_vs_tortuosity(cond: str, areas: np.ndarray, tort: np.ndarray, out_png: str):
    _ensure_figdir(os.path.dirname(out_png))
    if areas.size == 0 or tort.size == 0: return
    plt.figure(figsize=(6,4))
    plt.scatter(areas, tort, s=12, alpha=0.6)
    plt.xlabel("Convex-hull area (μm²)")
    plt.ylabel("Tortuosity (total / net)")
    plt.title(f"{cond} — Hull area vs. Tortuosity")
    plt.tight_layout(); plt.savefig(out_png, dpi=200); plt.close()

# ---------------- main HK1 runner ----------------

def run_hk1(inputs: list[str], outdir: str, px: float, dt: float, lag: int, minlen: int) -> None:
    """
    Clean/standardize input Traj_*.csv files and pool them by condition.
    Also compute per-track metrics and summary PNGs per condition.
    """
    os.makedirs(outdir, exist_ok=True)
    cleaned_dir       = os.path.join(outdir, "cleaned")
    pooled_dir        = os.path.join(outdir, "pooled")
    pooled_msd_dir    = os.path.join(outdir, "pooled_msd")
    track_metrics_dir = os.path.join(outdir, "pooled_tracks")
    fig_dir           = os.path.join(outdir, "figures")
    for d in (cleaned_dir, pooled_dir, pooled_msd_dir, track_metrics_dir, fig_dir):
        os.makedirs(d, exist_ok=True)

    trajs = _iter_traj_csvs(inputs)
    if not trajs:
        print("[HK1] No Traj_*.csv found in:", inputs)
        return

    pooled: Dict[str, List[pd.DataFrame]] = {}

    # --- clean per-file, tag, and pool
    for path in trajs:
        cond, date, rep = parse_condition_from_filename(path)
        try:
            df_raw = pd.read_csv(path, sep=None, engine="python")
        except Exception as e:
            print(f"[ERROR] {path}: failed to read CSV ({e})")
            continue

        try:
            sdf = _dedupe_and_standardize(df_raw)
        except Exception as e:
            print(f"[ERROR] {path}: {e}")
            continue

        # optional min length
        lens = sdf.groupby("track_id")["frame"].agg(lambda s: int(s.max() - s.min() + 1))
        keep_ids = lens.index[lens >= max(minlen, MIN_TRACK_LEN_FOR_METRICS)]
        sdf = sdf[sdf["track_id"].isin(keep_ids)].copy()

        sdf["__source_file"] = Path(path).name
        sdf["__condition"]   = cond
        sdf["__date"]        = date
        if rep is not None:
            sdf["__replicate"] = int(rep)

        cleaned_csv = os.path.join(cleaned_dir, Path(path).name.replace(".csv", "_clean.csv"))
        sdf.to_csv(cleaned_csv, index=False)

        pooled.setdefault(cond, []).append(sdf)

    # --- per-condition pooled outputs + metrics + figures
    for cond, parts in pooled.items():
        pooled_df = pd.concat(parts, ignore_index=True)
        if cond not in ALLOWED_CONDITIONS:
            print(f"[HK1][warn] condition '{cond}' not in allowed set {sorted(ALLOWED_CONDITIONS)}; pooling anyway.")

        # Save pooled trajectories
        pooled_csv = os.path.join(pooled_dir, f"Traj_{cond}_pooled.csv")
        pooled_df.to_csv(pooled_csv, index=False)

        # Per-track metrics (including new geometry & confinement)
        metrics_rows = []
        msd_tracks = []
        alpha2_tracks = []
        vacf_tracks = []
        lags_ref = None

        for tid, g in pooled_df.sort_values(["track_id","frame"]).groupby("track_id"):
            if len(g) < max(minlen, 2):
                continue

            # steps & summaries (pixels → μm at the very end when needed)
            steps_px = _steps_xy(g)
            mean_step_px = float(np.mean(steps_px)) if steps_px.size else np.nan
            rms_step_px  = float(np.sqrt(np.mean(steps_px**2))) if steps_px.size else np.nan

            # MSD & α
            lags, msd_um2 = _msd_track(g, px_um=px, max_lag=max(lag, DEFAULT_MAX_LAG))
            D_um2_s, alpha_hat = _fit_short_lag_powerlaw(lags, msd_um2, dt=dt, Lfit=min(3, len(lags)))

            # α2 vs lag
            lags_a2, a2 = _alpha2_vs_lag(g, px_um=px, max_lag=max(lag, DEFAULT_MAX_LAG))

            # VACF (normalized)
            lags_vacf, vacf = _vacf_normalized(g, px_um=px, dt=dt, max_lag=max(lag, DEFAULT_MAX_LAG))

            # Geometry: convex hull, path metrics
            xy_um = g[["x","y"]].to_numpy() * px
            hull = _convex_hull(xy_um)
            hull_area_um2, hull_per_um = _poly_area_perimeter(hull)
            total_path_um, net_disp_um = _path_length_and_net_disp(g, px_um=px)
            tortuosity = (total_path_um / (net_disp_um + 1e-12)) if net_disp_um > 0 else np.nan
            confinement_idx = 1.0 - (net_disp_um / (total_path_um + 1e-12)) if total_path_um > 0 else np.nan

            msd_tracks.append(msd_um2)
            alpha2_tracks.append(a2)
            vacf_tracks.append(vacf)
            lags_ref = lags  # same length across tracks

            metrics_rows.append({
                "track_id": int(tid),
                "n_frames": int(g["frame"].max() - g["frame"].min() + 1),
                "mean_step_px": mean_step_px,
                "rms_step_px": rms_step_px,
                "D_um2_per_s": D_um2_s,
                "alpha_hat": alpha_hat,
                "tortuosity": tortuosity,
                "confinement_index": confinement_idx,
                "hull_area_um2": hull_area_um2,
                "hull_perimeter_um": hull_per_um,
                "net_disp_um": net_disp_um,
                "total_path_um": total_path_um,
                "__condition": cond
            })

        # Write per-track metrics CSV
        metrics_df = pd.DataFrame(metrics_rows)
        metrics_csv = os.path.join(track_metrics_dir, f"track_metrics_{cond}.csv")
        metrics_df.to_csv(metrics_csv, index=False)

        # Pooled MSD table (lag, mean across tracks)
        if lags_ref is not None and msd_tracks:
            msd_mat = np.vstack([m[:len(lags_ref)] for m in msd_tracks])
            msd_mean = np.nanmean(msd_mat, axis=0)
            pooled_msd = pd.DataFrame({"lag": lags_ref, "msd_um2_mean": msd_mean})
            pooled_msd.to_csv(os.path.join(pooled_msd_dir, f"pooled_msd_{cond}.csv"), index=False)

            # Figures: MSD, α2, VACF
            fig_cond = os.path.join(fig_dir, f"{cond}_msd.png")
            _plot_msd_condition(cond, lags_ref, msd_tracks, fig_cond)

            fig_alpha2 = os.path.join(fig_dir, f"{cond}_alpha2.png")
            _plot_alpha2_condition(cond, lags_ref, alpha2_tracks, fig_alpha2)

            fig_vacf = os.path.join(fig_dir, f"{cond}_vacf.png")
            _plot_vacf_condition(cond, lags_ref - lags_ref.min() + 1, vacf_tracks, fig_vacf)  # lags for vacf use same scale

        # Steps / van Hove (lag=1)
        steps_all_um = []
        for _, g in pooled_df.sort_values(["track_id","frame"]).groupby("track_id"):
            s = _steps_xy(g) * px
            if s.size:
                steps_all_um.append(s)
        steps_all_um = np.concatenate(steps_all_um) if steps_all_um else np.array([])
        _plot_steps_condition(cond, steps_all_um, os.path.join(fig_dir, f"{cond}_steps.png"))
        _plot_vanhove_condition(cond, steps_all_um, os.path.join(fig_dir, f"{cond}_vanhove.png"))

        # Turning angles (on pooled, sorted by track)
        for_turn = pooled_df.sort_values(["track_id","frame"])
        _plot_angles_condition(cond, for_turn, os.path.join(fig_dir, f"{cond}_angles.png"))

        # Confinement index & hull area distributions; hull vs tortuosity scatter
        ci_vals = metrics_df["confinement_index"].to_numpy(dtype=float) if not metrics_df.empty else np.array([])
        areas   = metrics_df["hull_area_um2"].to_numpy(dtype=float) if not metrics_df.empty else np.array([])
        tort    = metrics_df["tortuosity"].to_numpy(dtype=float) if not metrics_df.empty else np.array([])
        _plot_confinement_hist(cond, ci_vals, os.path.join(fig_dir, f"{cond}_confinement.png"))
        _plot_hull_area_hist(cond, areas, os.path.join(fig_dir, f"{cond}_hull_area.png"))
        _plot_hull_vs_tortuosity(cond, areas, tort, os.path.join(fig_dir, f"{cond}_hull_vs_tortuosity.png"))

    print(f"[HK1] Cleaned {sum(len(v) for v in pooled.values())} file(s).")
    print(f"[HK1] Pooled trajectories  → {pooled_dir}")
    print(f"[HK1] Per-track metrics    → {track_metrics_dir}")
    print(f"[HK1] Pooled MSD tables    → {pooled_msd_dir}")
    print(f"[HK1] Figures              → {fig_dir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", help="Directory or Traj_*.csv files")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--px", type=float, default=0.1, help="microns per pixel")
    ap.add_argument("--dt", type=float, default=0.05, help="seconds per frame")
    ap.add_argument("--lag", type=int, default=DEFAULT_MAX_LAG, help="max lag for MSD/α2/VACF plots")
    ap.add_argument("--minlen", type=int, default=MIN_TRACK_LEN_FOR_METRICS, help="minimum frames per track to include")
    args = ap.parse_args()
    run_hk1(args.inputs, args.outdir, args.px, args.dt, args.lag, args.minlen)

if __name__ == "__main__":
    main()
