#!/usr/bin/env python3
"""
cli_autoprep.py
A thin wrapper around your gemspa CLI that auto-preps TrackMate folders if no Traj_*.csv are found.
Usage is identical to gemspa-cli; if needed it will call gemspa.trackmate_prep.cli_walk_and_prep()
before proceeding.
"""
import glob, os, sys
from argparse import ArgumentParser
from gemspa.trackmate_prep import cli_walk_and_prep
from gemspa.cli import main as gemspa_main  # reuse your existing CLI

def main():
    # Try the same arg parse as gemspa.cli, but intercept work_dir and csv-pattern
    parser = ArgumentParser()
    parser.add_argument("-d", "--work-dir", required=True)
    parser.add_argument("--csv-pattern", default="Traj_*.csv")
    args, _ = parser.parse_known_args()

    # If no Traj_* present, look for TrackMate and prep
    pattern = os.path.join(args.work_dir, args.csv_pattern)
    if not glob.glob(pattern):
        # look for any "Spots in tracks statistics.csv"
        tm_any = glob.glob(os.path.join(args.work_dir, "**", "*Spots in tracks*.csv"), recursive=True)
        if tm_any:
            print("[autoprep] No Traj_*.csv found; preparing TrackMate exports...")
            cli_walk_and_prep(args.work_dir)
        else:
            print("[autoprep] No Traj_* and no TrackMate exports detected. Proceeding anyway.")

    # hand off to the real CLI now that raw/Traj_* should exist
    return gemspa_main()

if __name__ == "__main__":
    sys.exit(main())
