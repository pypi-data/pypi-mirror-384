#!/usr/bin/env python3
# gemspa/trajectory_analysis.py  (flexible + TrackMate-aware)
import os, re, datetime
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from joblib import Parallel, delayed, parallel_backend
from multiprocessing import cpu_count

try:
    from .msd_diffusion import msd_diffusion
    from .rainbow_tracks import draw_rainbow_tracks
    from .trackmate_prep import find_trackmate_spots_csv, clean_trackmate_csv
except Exception:
    from msd_diffusion import msd_diffusion  # type: ignore
    def draw_rainbow_tracks(*args, **kwargs): print("[rainbow] skipped")
    from trackmate_prep import find_trackmate_spots_csv, clean_trackmate_csv  # type: ignore

REQUIRED = ('track_id','frame','x','y')

class trajectory_analysis:
    def __init__(
        self,
        data_file,
        results_dir='.',
        condition=None,
        time_step=0.010,
        micron_per_px=0.11,
        ts_resolution=0.005,
        min_track_len_linfit=11,
        tlag_cutoff_linfit=10,
        make_rainbow_tracks=False,
        img_file_prefix='MAX_',
        rainbow_min_D=0.0,
        rainbow_max_D=2.0,
        rainbow_colormap='viridis',
        rainbow_scale=1.0,
        rainbow_dpi=200,
        n_jobs=1,
        threads_per_rep=None,
        log_file=None
    ):
        self.n_jobs = n_jobs
        self.threads_per_rep = threads_per_rep or max(1, cpu_count() // max(1, n_jobs))
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

        # Accept a directory or a CSV. If directory or non-standard CSV is passed,
        # use TrackMate prep to clean while preserving extra columns.
        in_path = str(data_file)
        pick = find_trackmate_spots_csv(in_path) or in_path
        if os.path.isdir(in_path):
            data_file = pick  # chosen spots csv
        # Read and canonicalize
        try:
            raw = pd.read_csv(data_file, sep=None, engine='python')
        except Exception:
            raw = pd.read_csv(data_file)
        df = clean_trackmate_csv(data_file) if not set(REQUIRED).issubset({c.lower() for c in raw.columns}) else raw
        # Final guards / sort
        cols_lower = {c.lower(): c for c in df.columns}
        for need in REQUIRED:
            if need not in cols_lower:
                raise KeyError(f"Required column '{need}' missing after cleaning.")
        # normalize names
        df.rename(columns={cols_lower['track_id']:'track_id',
                           cols_lower['frame']:'frame',
                           cols_lower['x']:'x',
                           cols_lower['y']:'y'}, inplace=True)
        df[['track_id','frame','x','y']] = df[['track_id','frame','x','y']].apply(pd.to_numeric, errors='coerce')
        df = df.dropna(subset=['track_id','frame','x','y']).copy()
        df['track_id'] = df['track_id'].astype('int64')
        df = df.sort_values(['track_id','frame']).copy()

        base = os.path.splitext(os.path.basename(data_file))[0]
        self.condition            = condition or re.sub(r'_[0-9]+$', '', base)
        self.time_step            = time_step
        self.micron_per_px        = micron_per_px
        self.ts_resolution        = ts_resolution
        self.min_track_len_linfit = min_track_len_linfit
        self.tlag_cutoff_linfit   = tlag_cutoff_linfit
        self.make_rainbow_tracks  = make_rainbow_tracks
        self.img_prefix           = img_file_prefix
        self.rainbow_min_D        = rainbow_min_D
        self.rainbow_max_D        = rainbow_max_D
        self.rainbow_colormap     = rainbow_colormap
        self.rainbow_scale        = rainbow_scale
        self.rainbow_dpi          = rainbow_dpi
        self.rainbow_line_width   = 0.1

        self.raw_df = df.copy()
        self.raw_df['condition'] = self.condition
        self.msd_processor = msd_diffusion(save_dir=self.results_dir)

        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log = open(os.path.join(self.results_dir, f"{base}_{ts}.log"), 'w')

    @staticmethod
    def _compute_msd(coords, max_lag):
        n = coords.shape[0]
        out = np.zeros(max_lag)
        for lag in range(1, max_lag+1):
            d = coords[lag:] - coords[:n-lag]
            out[lag-1] = np.mean(d[:,0]**2 + d[:,1]**2) if d.size else 0.0
        return out

    def _one_track(self, grp: pd.DataFrame):
        coords = grp[['x','y']].to_numpy() * self.micron_per_px
        L = min(self.tlag_cutoff_linfit, max(1, coords.shape[0]-1))
        return self._compute_msd(coords, L)

    def _fit_D_alpha_from_loglog(self, tau, msd):
        m = (tau>0) & (msd>0)
        if m.sum() < 2: return 0.0, 0.0
        a, b = np.polyfit(np.log10(tau[m]), np.log10(msd[m]), 1)
        return float((10.0**b)/4.0), float(a)

    def calculate_msd_and_diffusion(self):
        tracks = [g for _,g in self.raw_df.groupby('track_id') if len(g) >= self.min_track_len_linfit]
        if not tracks:
            raise RuntimeError(f"No tracks pass min length >= {self.min_track_len_linfit}")
        from joblib import Parallel, delayed, parallel_backend
        with parallel_backend('threading'):
            msd_list = Parallel(n_jobs=self.threads_per_rep)(delayed(self._one_track)(g) for g in tracks)
        L = min(len(v) for v in msd_list)
        tau = np.arange(1, L+1, dtype=float) * self.time_step
        msd_mat = np.vstack([v[:L] for v in msd_list])
        ens = np.nanmean(msd_mat, axis=0)
        # plots
        self._plot_linear(tau, ens, out=os.path.join(self.results_dir,'msd_vs_tau.png'))
        self._plot_loglog(tau, ens, out=os.path.join(self.results_dir,'msd_vs_tau_loglog.png'))
        # per-track fits via msd_processor for compatibility
        rows = []
        for grp, vec in zip(tracks, msd_list):
            D, alpha, r2 = self.msd_processor.fit_msd(vec, self.time_step)
            rows.append((int(grp['track_id'].iloc[0]), D, alpha, r2))
        ids, Dv, Av, Rv = zip(*rows)
        self.results_df = pd.DataFrame({'track_id':ids, 'condition':self.condition, 'D_fit':Dv, 'alpha_fit':Av, 'r2_fit':Rv})
        self.results_df.to_csv(os.path.join(self.results_dir,'msd_results.csv'), index=False)
        self.make_plot(); self.make_scatter()

    def _plot_linear(self, tau, msd, out):
        fig, ax = plt.subplots(figsize=(9,5)); ax.plot(tau, msd, 'o', ms=3)
        m = (tau>0) & (msd>0); D = (np.polyfit(tau[m], msd[m], 1)[0]/4.0) if m.sum()>=2 else 0.0
        ax.set_xlabel('τ (s)'); ax.set_ylabel('MSD (μm²)'); ax.set_title(f'ens-avg MSD  D≈{D:.3g} μm²/s')
        fig.tight_layout(); fig.savefig(out, dpi=300); plt.close(fig)

    def _plot_loglog(self, tau, msd, out):
        fig, ax = plt.subplots(figsize=(9,5))
        m = (tau>0) & (msd>0); ax.plot(np.log10(tau[m]), msd[m], 'o', ms=3); ax.set_yscale('log')
        a = np.polyfit(np.log10(tau[m]), np.log10(msd[m]), 1)[0] if m.sum()>=2 else 0.0
        ax.set_xlabel('log10 τ (s)'); ax.set_ylabel('MSD (μm²)'); ax.set_title(f'ens-avg log–log MSD  α≈{a:.3g}')
        fig.tight_layout(); fig.savefig(out, dpi=300); plt.close(fig)

    def export_step_sizes(self, max_tlag=None):
        df = self.raw_df[['track_id','frame','x','y']].copy()
        df['x'] *= self.micron_per_px; df['y'] *= self.micron_per_px
        arr = df.sort_values(['track_id','frame']).to_numpy()
        self.msd_processor.set_track_data(arr)
        if max_tlag is not None: self.msd_processor.max_tlag_step_size = max_tlag
        self.msd_processor.step_sizes_and_angles()
        ss = self.msd_processor.save_step_sizes(file_name='all_data_step_sizes.txt')
        ss = ss.rename(columns={'t':'tlag'}); ss.insert(1,'group', self.condition)
        out = os.path.join(self.results_dir,'all_data_step_sizes.txt')
        ss.to_csv(out, sep='\t', index=False)

    def make_plot(self):
        fig, ax = plt.subplots(figsize=(8,5))
        d = self.results_df['D_fit']; dpos = d[d>0]
        bins = (np.logspace(np.log10(max(dpos.min(),1e-6)), np.log10(dpos.max()), 30) if len(dpos) else 30)
        if len(dpos): ax.set_xscale('log')
        ax.hist(d, bins=bins, edgecolor='black'); ax.set_xlabel('D_fit (μm²/s)'); ax.set_title(f'D_fit ({self.condition})')
        fig.tight_layout(); fig.savefig(os.path.join(self.results_dir,'D_fit_distribution.png')); plt.close(fig)

    def make_scatter(self):
        fig, ax = plt.subplots(figsize=(8,5))
        d = self.results_df['D_fit'].replace({0: np.nan})
        ax.scatter(np.log10(d), self.results_df['alpha_fit'], alpha=0.6)
        ax.set_xlabel('log10(D_fit)'); ax.set_ylabel('alpha_fit'); ax.set_title(f'α vs log D ({self.condition})')
        fig.tight_layout(); fig.savefig(os.path.join(self.results_dir,'alpha_vs_logD.png')); plt.close(fig)

    def write_params_to_log_file(self):
        import pandas as pd
        params = {'condition': self.condition, 'time_step': self.time_step,
                  'micron_per_px': self.micron_per_px,
                  'min_track_len_linfit': self.min_track_len_linfit,
                  'tlag_cutoff_linfit': self.tlag_cutoff_linfit}
        pd.Series(params).to_csv(os.path.join(self.results_dir,'params_log.csv'), header=False)
        with open(os.path.join(self.results_dir,'params_log.txt'), 'w') as f:
            for k,v in params.items(): f.write(f"{k}: {v}\n")
