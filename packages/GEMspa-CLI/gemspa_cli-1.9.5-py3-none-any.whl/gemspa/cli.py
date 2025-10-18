#!/usr/bin/env python3
import argparse, os, re, sys, multiprocessing as mp
from pathlib import Path

from .trajectory_analysis import trajectory_analysis
from .ensemble_analysis import run_ensemble
from .step_size_analysis import run_step_size_analysis_if_requested as run_step_size_analysis

from . import trackmateclean as tmc
from . import hk1_trackmate_analysis as hk1

def _cpu_count():
    try:
        return mp.cpu_count()
    except Exception:
        return 4

def run_per_replicate(*, work_dir, csv_glob, time_step, micron_per_px, ts_resolution,
                      min_track_len, tlag_cutoff, rainbow_tracks, img_prefix,
                      rainbow_min_D, rainbow_max_D, rainbow_colormap, rainbow_scale, rainbow_dpi,
                      n_jobs, threads_per_rep, filter_D_min, filter_D_max, filter_alpha_min, filter_alpha_max):
    import glob, os
    files = sorted(glob.glob(os.path.join(work_dir, csv_glob)))
    if not files:
        print(f"[gemspa] No files match {csv_glob} in {work_dir}")
        return
    for f in files:
        outdir = os.path.join(work_dir, os.path.splitext(os.path.basename(f))[0])
        ta = trajectory_analysis(
            data_file=f, results_dir=outdir,
            time_step=time_step, micron_per_px=micron_per_px, ts_resolution=ts_resolution,
            min_track_len_linfit=min_track_len, tlag_cutoff_linfit=tlag_cutoff,
            make_rainbow_tracks=rainbow_tracks, img_file_prefix=(img_prefix or "MAX_"),
            rainbow_min_D=(rainbow_min_D if rainbow_min_D is not None else 0.0),
            rainbow_max_D=(rainbow_max_D if rainbow_max_D is not None else 2.0),
            rainbow_colormap=rainbow_colormap, rainbow_scale=1.0 if rainbow_scale=="linear" else rainbow_scale,
            rainbow_dpi=rainbow_dpi, n_jobs=n_jobs, threads_per_rep=threads_per_rep
        )
        ta.calculate_msd_and_diffusion()


def main():
    ap = argparse.ArgumentParser(
        prog="gemspa-cli",
        description="GEMspa Single-Particle Tracking Analysis CLI"
    )
    ap.add_argument("-d", "--work-dir", required=True, help="Directory with CSV trajectory files")
    ap.add_argument("--csv-pattern", default="Traj_*.csv",
                    help="Glob for input CSVs (default: Traj_*.csv). Examples: '*Spots in tracks*.csv' for TrackMate.")
    ap.add_argument("-j", "--n-jobs", type=int, default=max(1, _cpu_count()//2),
                    help="Parallel processes (across replicates)")
    ap.add_argument("--threads-per-rep", type=int, default=None,
                    help="Threads per replicate (default=cores / n_jobs)")
    ap.add_argument("--time-step", type=float, help="")
    ap.add_argument("--micron-per-px", type=float, help="")
    ap.add_argument("--ts-resolution", type=float, help="")
    ap.add_argument("--min-track-len", type=int, default=3)
    ap.add_argument("--tlag-cutoff", type=int, default=3)

    # Rainbow tracks / imaging options
    ap.add_argument("--rainbow-tracks", action="store_true")
    ap.add_argument("--img-prefix", default=None)
    ap.add_argument("--rainbow-min-D", type=float, default=None)
    ap.add_argument("--rainbow-max-D", type=float, default=None)
    ap.add_argument("--rainbow-colormap", default="viridis")
    ap.add_argument("--rainbow-scale", default="linear")
    ap.add_argument("--rainbow-dpi", type=int, default=150)

    # Filters (shared across pipeline)
    ap.add_argument("--filter-D-min", type=float, default=None)
    ap.add_argument("--filter-D-max", type=float, default=None)
    ap.add_argument("--filter-alpha-min", type=float, default=None)
    ap.add_argument("--filter-alpha-max", type=float, default=None)

    # Optional analyses
    ap.add_argument("--step-size-analysis", action="store_true",
                    help="Also run the step-size KDE & KS analysis (ensemble stage)")

    # ---- TrackMate cleaner (standalone; exits after running) ----
    ap.add_argument("--clean-trackmate", action="store_true",
                    help="Run the packaged TrackMate cleaner on WORK_DIR and exit (no GEMspa analysis).")
    ap.add_argument("--clean-out-dir", default=None,
                    help="When using --clean-trackmate, write cleaned outputs here (flat).")
    ap.add_argument("--clean-include-date", action="store_true",
                    help="When cleaning, name outputs as Traj_<COND>-<DATE>_<REP>.csv (default pools days: Traj_<COND>_<REP>.csv).")
    ap.add_argument("--clean-date-format", choices=["YYMMDD","YYYYMMDD"], default="YYMMDD",
                    help="Date code format for --clean-include-date.")
    ap.add_argument("--clean-move", action="store_true",
                    help="When fixing legacy Traj_* names, move instead of copy.")
    ap.add_argument("--clean-dry-run", action="store_true",
                    help="Cleaner: print actions only.")

    # ---- HK1 control: ON by default; use --no-HK1 to skip ----
    ap.add_argument("--no-HK1", action="store_true",
                    help="Disable the automatic HK1 grouped analysis.")
    ap.add_argument("--HK1", action="store_true", help=argparse.SUPPRESS)

    args = ap.parse_args()
    work_dir = os.path.abspath(args.work_dir)

    # Standalone cleaner path
    if args.clean_trackmate:
        tmc.run_clean(
            root=work_dir,
            out_dir=args.clean_out_dir,
            include_date=args.clean_include_date,
            date_format=args.clean_date_format,
            move=args.clean_move,
            dry_run=args.clean_dry_run,
        )
        print("[clean-trackmate] Done.")
        return 0

    # ---------- Normal GEMspa pipeline ----------
    csv_glob = args.csv_pattern
    n_jobs = int(args.n_jobs)
    threads_per_rep = args.threads_per_rep or max(1, _cpu_count() // max(1, n_jobs))

    # Per-replicate analysis
    run_per_replicate(
        work_dir=work_dir,
        csv_glob=csv_glob,
        time_step=args.time_step,
        micron_per_px=args.micron_per_px,
        ts_resolution=args.ts_resolution,
        min_track_len=args.min_track_len,
        tlag_cutoff=args.tlag_cutoff,
        rainbow_tracks=args.rainbow_tracks,
        img_prefix=args.img_prefix,
        rainbow_min_D=args.rainbow_min_D,
        rainbow_max_D=args.rainbow_max_D,
        rainbow_colormap=args.rainbow_colormap,
        rainbow_scale=args.rainbow_scale,
        rainbow_dpi=args.rainbow_dpi,
        n_jobs=n_jobs,
        threads_per_rep=threads_per_rep,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
    )

    # Ensemble analysis & comparisons
    run_ensemble(
        work_dir=work_dir,
        time_step=args.time_step,
        micron_per_px=args.micron_per_px,
        tlag_cutoff=args.tlag_cutoff,
        min_track_len=args.min_track_len,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
        run_step_sizes=args.step_size_analysis,   # flag controls ensemble KDEs
    )

    # ---- Automatic HK1 grouped analysis (unless opted out) ----
    if not args.no_HK1:
        hk1_outdir = os.path.join(work_dir, "grouped_advanced_analysis")
        inputs = [work_dir]
        # cascade defaults (consistent with per-rep/ensemble)
        dt  = args.time_step      if args.time_step      is not None else 0.03
        px  = args.micron_per_px  if args.micron_per_px  is not None else 0.1
        lag = args.tlag_cutoff    if args.tlag_cutoff    is not None else 3
        minlen = args.min_track_len if args.min_track_len is not None else 3

        print(f"[HK1] Running grouped analysis → {hk1_outdir}")
        hk1.run_hk1(
            inputs=inputs,
            outdir=hk1_outdir,
            px=px,
            dt=dt,
            lag=lag,
            minlen=minlen,
            # forward the SAME filters to HK1 stage for full consistency
            filter_D_min=args.filter_D_min,
            filter_D_max=args.filter_D_max,
            filter_alpha_min=args.filter_alpha_min,
            filter_alpha_max=args.filter_alpha_max,
        )
    else:
        print("[HK1] Skipped by --no-HK1")

    return 0

if __name__ == "__main__":
    sys.exit(main())
