#!/usr/bin/env python3
# gemspa/cli.py  — autoprep + HK1 integrated, compatible with existing flags

import argparse
import glob
import os
import re
import shlex
import sys
import subprocess
from functools import partial
from multiprocessing import Pool, cpu_count
from pathlib import Path

# Package imports (same as your current CLI)
from gemspa.trajectory_analysis import trajectory_analysis
from gemspa.step_size_analysis import run_step_size_analysis_if_requested
from gemspa.ensemble_analysis import run_ensemble
from gemspa.compare_conditions import compare_conditions

# TrackMate autoprep utilities
try:
    from gemspa.trackmate_prep import cli_walk_and_prep
except Exception:
    cli_walk_and_prep = None


def _process_replicate(args, csv_file):
    base = os.path.basename(csv_file)
    name, _ = os.path.splitext(base)

    # Replicate name & condition parsing (works with and without 'Traj_' prefix)
    replicate = name.replace("Traj_", "") if name.startswith("Traj_") else name
    condition = re.sub(r"_[0-9]+$", "", replicate)

    result_dir = os.path.join(args.work_dir, replicate)
    os.makedirs(result_dir, exist_ok=True)

    # threads per replicate
    tpr = args.threads_per_rep if args.threads_per_rep is not None else max(
        1, cpu_count() // max(1, args.n_jobs)
    )

    ta = trajectory_analysis(
        data_file=csv_file,
        results_dir=result_dir,
        condition=condition,
        time_step=args.time_step,
        micron_per_px=args.micron_per_px,
        ts_resolution=args.ts_resolution,
        min_track_len_linfit=args.min_track_len,
        tlag_cutoff_linfit=args.tlag_cutoff,
        make_rainbow_tracks=args.rainbow_tracks,
        img_file_prefix=args.img_prefix,
        rainbow_min_D=args.rainbow_min_D,
        rainbow_max_D=args.rainbow_max_D,
        rainbow_colormap=args.rainbow_colormap,
        rainbow_scale=args.rainbow_scale,
        rainbow_dpi=args.rainbow_dpi,
        n_jobs=args.n_jobs,
        threads_per_rep=tpr,
    )

    ta.write_params_to_log_file()
    ta.calculate_msd_and_diffusion()

    if args.step_size_analysis:
        ta.export_step_sizes()
        run_step_size_analysis_if_requested(result_dir)


def _find_inputs(work_dir: str, csv_pattern: str):
    """Recursive search first; fall back to non-recursive to match legacy behavior."""
    pat_recursive = os.path.join(work_dir, "**", csv_pattern)
    files = sorted(glob.glob(pat_recursive, recursive=True))
    if files:
        return files
    # legacy (flat) search
    pat_flat = os.path.join(work_dir, csv_pattern)
    return sorted(glob.glob(pat_flat))


def main():
    parser = argparse.ArgumentParser(
        description="GEMspa Single-Particle Tracking Analysis CLI"
    )
    parser.add_argument(
        "-d",
        "--work-dir",
        required=True,
        help="Directory with CSV trajectory files (or TrackMate exports)",
    )
    parser.add_argument(
        "--csv-pattern",
        default="Traj_*.csv",
        help="Glob for input CSVs (default: Traj_*.csv). Examples: '*Spots in tracks*.csv' for TrackMate.",
    )
    parser.add_argument(
        "-j",
        "--n-jobs",
        type=int,
        default=cpu_count(),
        help="Parallel processes (across replicates)",
    )
    parser.add_argument(
        "--threads-per-rep",
        type=int,
        default=None,
        help="Threads per replicate (default=cores / n_jobs)",
    )

    # Core SPT / MSD params
    parser.add_argument("--time-step", type=float, default=0.010)
    parser.add_argument("--micron-per-px", type=float, default=0.11)
    parser.add_argument("--ts-resolution", type=float, default=0.005)
    parser.add_argument("--min-track-len", type=int, default=11)
    parser.add_argument("--tlag-cutoff", type=int, default=10)

    # Rainbow overlays (preserve your existing flags)
    parser.add_argument("--rainbow-tracks", action="store_true")
    parser.add_argument("--img-prefix", default="MAX_")
    parser.add_argument("--rainbow-min-D", type=float, default=0.0)
    parser.add_argument("--rainbow-max-D", type=float, default=2.0)
    parser.add_argument("--rainbow-colormap", default="viridis")
    parser.add_argument("--rainbow-scale", type=float, default=1.0)
    parser.add_argument("--rainbow-dpi", type=int, default=200)

    # Ensemble filtering & compare (preserve existing defaults)
    parser.add_argument("--filter-D-min", type=float, default=0.001)
    parser.add_argument("--filter-D-max", type=float, default=2.0)
    parser.add_argument("--filter-alpha-min", type=float, default=0.0)
    parser.add_argument("--filter-alpha-max", type=float, default=2.0)

    # Step-size analysis
    parser.add_argument(
        "--step-size-analysis",
        action="store_true",
        help="Also run the step-size KDE & KS analysis",
    )

    # NEW: optional HK1 pass
    parser.add_argument(
        "--HK1",
        action="store_true",
        help="Run HK1 analysis on the same inputs after core GEMspa steps",
    )

    args = parser.parse_args()
    work_dir = os.path.abspath(args.work_dir)
    os.makedirs(work_dir, exist_ok=True)

    # 1) Discover CSVs
    csvs = [f for f in _find_inputs(work_dir, args.csv_pattern) if os.path.getsize(f) > 0]

    # 2) If none, attempt TrackMate autoprep -> raw/Traj_*.csv
    if not csvs:
        # broaden detection: tracks vs track
        tm_hits = _find_inputs(work_dir, "*Spots in tracks*.csv")
        tm_hits += [f for f in _find_inputs(work_dir, "*Spots in track*.csv") if f not in tm_hits]
        if tm_hits and cli_walk_and_prep:
            print("[autoprep] TrackMate exports detected; preparing standardized CSVs under <work-dir>/raw ...")
            cli_walk_and_prep(work_dir)
            # after prep, look under raw/ by default
            csvs = _find_inputs(work_dir, "raw/Traj_*.csv")
        else:
            parser.exit(message=f"No files matching {args.csv_pattern!r} in {args.work_dir}\n")

    if not csvs:
        parser.exit(message=f"No usable inputs found in {args.work_dir}\n")

    # 3) Per-replicate processing
    if args.n_jobs > 1:
        with Pool(args.n_jobs) as pool:
            pool.map(partial(_process_replicate, args), csvs)
    else:
        for f in csvs:
            _process_replicate(args, f)

    # 4) Grouping + ensemble plots
    run_ensemble(
        args.work_dir,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
        time_step=args.time_step,
        micron_per_px=args.micron_per_px,
        tlag_cutoff=args.tlag_cutoff,
        min_track_len=args.min_track_len,
    )

    compare_conditions(
        args.work_dir,
        filter_D_min=args.filter_D_min,
        filter_D_max=args.filter_D_max,
        filter_alpha_min=args.filter_alpha_min,
        filter_alpha_max=args.filter_alpha_max,
    )

    # 5) Optional HK1 pass, writing under <work-dir>/hk1_results
    if args.HK1:
        hk1_out = os.path.join(work_dir, "hk1_results")
        os.makedirs(hk1_out, exist_ok=True)

        # Try namespaced import first (file is inside the package)
        try:
            import gemspa.hk1_trackmate_analysis as hk1
            if hasattr(hk1, "run_hk1"):
                inputs = [os.path.join(work_dir, "raw")] if os.path.isdir(os.path.join(work_dir, "raw")) else [work_dir]
                hk1.run_hk1(
                    inputs=inputs,
                    outdir=hk1_out,
                    px=args.micron_per_px,
                    dt=args.time_step,
                    lag=1,
                    minlen=max(3, args.min_track_len),
                )
            else:
                raise ImportError("gemspa.hk1_trackmate_analysis.run_hk1 not found")
        except Exception:
            # Fallback 1: try top-level module (dev checkouts)
            try:
                import hk1_trackmate_analysis as hk1
                if hasattr(hk1, "run_hk1"):
                    inputs = [os.path.join(work_dir, "raw")] if os.path.isdir(os.path.join(work_dir, "raw")) else [work_dir]
                    hk1.run_hk1(
                        inputs=inputs,
                        outdir=hk1_out,
                        px=args.micron_per_px,
                        dt=args.time_step,
                        lag=1,
                        minlen=max(3, args.min_track_len),
                    )
                else:
                    raise ImportError("hk1_trackmate_analysis.run_hk1 not found")
            except Exception:
                # Fallback 2: run the script next to this CLI inside the installed package
                pkg_dir = Path(__file__).resolve().parent
                hk1_script = pkg_dir / "hk1_trackmate_analysis.py"
                if hk1_script.exists():
                    cmd = [
                        sys.executable,
                        str(hk1_script),
                        os.path.join(work_dir, "raw") if os.path.isdir(os.path.join(work_dir, "raw")) else work_dir,
                        "--outdir",
                        hk1_out,
                        "--px",
                        str(args.micron_per_px),
                        "--dt",
                        str(args.time_step),
                        "--lag",
                        "1",
                        "--minlen",
                        str(max(3, args.min_track_len)),
                    ]
                    print("[HK1]", " ".join(map(shlex.quote, cmd)))
                    subprocess.run(cmd, check=False)
                else:
                    print("[HK1] hk1_trackmate_analysis.py not found in package; skipping HK1.")

if __name__ == "__main__":
    main()
