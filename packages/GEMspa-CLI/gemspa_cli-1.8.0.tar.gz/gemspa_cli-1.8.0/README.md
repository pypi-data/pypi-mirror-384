# GEMspa-CLI: Single-Particle Tracking Analysis

Version 1.6

CLI for the GEMspa analysis pipeline (based on Keegan *et al.*), with extras for TrackMate input, colored track overlays, MSD-vs-τ plots, and ensemble step-size analysis.

---

## 1) Create a virtual environment (recommended)

```bash
# macOS/Linux
python3 -m venv ~/venvs/gemspa && source ~/venvs/gemspa/bin/activate

# Windows (PowerShell)
python -m venv %USERPROFILE%\venvs\gemspa
%USERPROFILE%\venvs\gemspa\Scripts\Activate.ps1
```

You can deactivate any time with `deactivate`.

---

## 2) Install the package

From PyPI/TestPyPI (adjust the index as needed):

```bash
python -m pip install --upgrade pip
python -m pip install gemspa-cli
```

Or from a local checkout (repo root where `pyproject.toml` lives):

```bash
python -m pip install -e .
```

---

## 3) Run the CLI

Basic pattern:

```bash
gemspa-cli \
  -d /path/to/folder/with/CSVs \
  [options]
```

### Required

- **`-d`, `--work-dir`**: directory containing your trajectory CSVs (non-recursive by default).

### Common options

**Input discovery**
- `--csv-pattern "Traj_*.csv"`: glob for input CSVs (default shown). For TrackMate, e.g. `--csv-pattern "*Spots in tracks*.csv"`.

**Acquisition / units**
- `--time-step 0.010` (seconds between frames; default 0.01 s).
- `--micron-per-px 0.11` (µm per pixel; default 0.11).

**Track/fit constraints**
- `--min-track-len 11` (minimum frames per track to fit).
- `--tlag-cutoff 10` (maximum lag, in frames, to use when building MSD).

**Parallelism**
- `-j`, `--n-jobs` (processes across replicates; default = CPU cores).
- `--threads-per-rep` (threads used inside each replicate; default ≈ cores/`n_jobs`).

**Rainbow track overlays (optional)**
- `--rainbow-tracks` to enable.
- `--img-prefix MAX_`, `--rainbow-min-D`, `--rainbow-max-D`, `--rainbow-colormap`, `--rainbow-scale`, `--rainbow-dpi`.

**Ensemble filtering**
- `--filter-D-min 0.001`, `--filter-D-max 2.0`,
- `--filter-alpha-min 0.0`, `--filter-alpha-max 2.0`.
  Used when pooling replicates per condition and for comparison plots.

**Step-size analysis**
- `--step-size-analysis` to export per-replicate step sizes and KDE plots; ensemble step-size plots are produced during the ensemble step.

### Example runs

```bash
# Minimal run
gemspa-cli -d /data/spa_runs

# With TrackMate CSVs
gemspa-cli -d /data/spa_runs --csv-pattern "*Spots in tracks*.csv" --micron-per-px 1.0

# With rainbow overlays and step-size analysis
gemspa-cli -d /data/spa_runs --rainbow-tracks --step-size-analysis
```

---

## 4) Inputs (format & organization)

- **Where to put files**: place all CSVs directly in `--work-dir` (non-recursive search by default). The ensemble step will also look one level down inside replicate folders created by the run.
- **CSV schema (case-insensitive)**: `track_id`, `frame`, `x`, `y`. TrackMate aliases are accepted (e.g., `trajectory`→`track_id`, `POSITION_X`→`x`, `SPOT_FRAME`→`frame`). Delimiter is auto-detected. Units: `x,y` in pixels; conversion uses `--micron-per-px`.
- **Condition/replicate naming**: filenames like `Traj_<condition>_<rep>.csv` (e.g., `Traj_DMSO_001.csv`). Condition = stem without trailing `_<rep>`.
- **Images for overlays (optional)**: place `MAX_<condition>_<rep>.tif` next to the CSVs (or `MAX_<condition>.tif`, `MAX_<condition>*`).

---

## 5) Outputs (what you’ll see)

### Per replicate (a subfolder is created per input file)
- `msd_results.csv` with per-track fits: **D_fit**, **alpha_fit**, **r2_fit**.
- **Distributions/Scatter**:
  - `D_fit_distribution.png` (log-spaced histogram of D).
  - `alpha_vs_logD.png` (scatter of α vs log10 D).
- **Per-file MSD vs τ**:
  - `msd_vs_tau.png` (linear MSD vs τ with D estimate).
  - `msd_vs_tau_loglog.png` (log-log MSD vs τ with α slope).
- **Rainbow overlay (optional)**: `rainbow_tracks.png` with tracks colored by D.

### Ensemble (pooled per condition)
- **Tables**:
  - `grouped_raw/msd_results.csv` (all tracks kept by per-replicate filters).
  - `grouped_filtered/msd_results.csv` (tracks within ensemble D/α bounds).
- **Ensemble MSD vs τ** (condition-level):
  - `grouped_raw/ensemble_msd_vs_tau_<condition>.png`
  - `grouped_raw/ensemble_msd_vs_tau_loglog_<condition>.png`
  - `grouped_filtered/ensemble_msd_vs_tau_<condition>.png`
  - `grouped_filtered/ensemble_msd_vs_tau_loglog_<condition>.png`
- **Ensemble step-size KDEs**:
  - RAW: `grouped_raw/step_kde/step_kde_<condition>_(ensemble).png`
  - FILTERED: `grouped_filtered/step_kde/step_kde_<condition>_(filtered_ensemble).png`
- **Cross-condition comparison** (from filtered pool):
  - `comparison/ensemble_filtered_D_histograms.png` (log-x, means, KS asterisks)
  - `comparison/ensemble_filtered_alpha_histograms.png`
  - `comparison/replicate_median_D_boxplot.png` (with hue fix)

---

## 6) Script components & math/algorithms

- **`gemspa/cli.py`** – orchestrates the run: discovers CSVs, spawns per-replicate jobs, runs optional step-size, then assembles ensembles and comparison plots. Key flags: `--work-dir` (`-d`), `--csv-pattern`, `--min-track-len`, `--tlag-cutoff`, rainbow options, and filter bounds.

- **`gemspa/trajectory_analysis.py`** – per-file pipeline:
  - Loads CSV (TrackMate-friendly headers), groups by `track_id`.
  - Computes MSD per track up to `tlag_cutoff`.
  - Fits **MSD(t) = 4·D·t^α** (nonlinear; linear fallback sets α≈1).
  - Saves per-track `msd_results.csv`, distribution and scatter plots; optional `rainbow_tracks.png`.
  - Also saves per-file **MSD vs τ** and **log-log MSD vs τ** plots.

- **`gemspa/msd_diffusion.py`** – optimized MSD/fit helpers:
  - Numba-JIT 2D MSD for speed.
  - Nonlinear fit to **MSD(t) = 4·D·t^α**; linear fallback **MSD(t)=4·D·t**.
  - Step-size/angle exports used by the KDE step.

- **`gemspa/rainbow_tracks.py`** – draws line segments per trajectory onto `MAX_*.tif` and colors by **D_fit** (clamped to `[--rainbow-min-D, --rainbow-max-D]`, selectable colormap).

- **`gemspa/step_size_analysis.py`** – step-size KDEs & statistics:
  - Accepts “long” (`group,tlag,step_size`) or converts “wide” to long.
  - Per-replicate KDEs (log-y) color-coded by τ using a color-blind palette; annotates non-Gaussian parameter **α₂ = ⟨r⁴⟩/(3⟨r²⟩²) − 1**.
  - KS “volcano” plot of `−log10 p` vs τ for two groups.
  - **Ensemble KDEs**: aggregates all replicate step files (RAW) and recomputes step sizes restricted to filtered track IDs (FILTERED).

- **`gemspa/ensemble_analysis.py`** – per-condition pooling:
  - Reads replicate `msd_results.csv`, applies D/α bounds, writes grouped tables.
  - Builds **ensemble MSD vs τ** (linear & log-log) for RAW and FILTERED pools.
  - Calls the ensemble step-size KDEs (RAW & FILTERED).

- **`gemspa/compare_conditions.py`** – cross-condition visuals from the FILTERED pool:
  - Overlaid histograms for D (log-x) and α with mean lines and KS test asterisks.
  - Boxplot of replicate median D with jittered points (hue fix to avoid seaborn warning).

---

### Notes & tips

- The CLI does **not** recurse into subfolders when discovering input CSVs (unless your `--csv-pattern` points there). It **does** look one level down for replicate outputs when assembling ensembles.
- TrackMate CSVs work via `--csv-pattern` and header mapping; if positions are already in µm, use `--micron-per-px 1.0`.
- Long plot titles are auto-wrapped and saved with tight bounding boxes to avoid clipping.
