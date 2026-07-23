"""
Per-session linear regression, then a group-level summary.

Read this as the template: pure functions on DataFrames at the top, one thin
`run_pipeline` at the bottom that wires io -> analysis -> disk.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ..io import datasets as _io
from ..settings import Paths
from ..utils.fitting import fit_line
from ..utils.stats import bootstrap_ci, sem

__all__ = ["fit_per_session", "summarize_sessions", "run_pipeline"]

RESULTS_NAME = "session_fits"


def fit_per_session(df: pd.DataFrame, *, x: str = "x", y: str = "y",
                    by: str = "session", min_trials: int = 10) -> pd.DataFrame:
    """
    Fit one line per session.

    Sessions with fewer than `min_trials` usable trials are skipped rather than
    fitted badly; the count of skipped sessions is available as an attribute on
    the returned frame (`.attrs['n_skipped']`).

    Returns one row per session: session, intercept, slope, r2, *_se, n,
    slope_lo/slope_hi (95% t interval), plus the ground-truth columns.
    """
    rows, skipped = [], 0
    for key, g in df.groupby(by, sort=True):
        if len(g) < min_trials:
            skipped += 1
            continue
        f = fit_line(g[x].to_numpy(), g[y].to_numpy())
        lo, hi = f.slope_ci()
        rec = {by: key, **f.as_dict(), "slope_lo": lo, "slope_hi": hi}
        for truth in ("true_intercept", "true_slope"):
            if truth in g.columns:
                rec[truth] = float(g[truth].iloc[0])
        rows.append(rec)

    out = pd.DataFrame(rows)
    out.attrs["n_skipped"] = skipped
    return out


def summarize_sessions(fits: pd.DataFrame, *, rng: int = 0) -> dict:
    """
    Group-level summary of the per-session fits.

    Bootstrap CIs are seeded (`rng`) so the numbers are reproducible.
    """
    if fits.empty:
        raise ValueError("no session fits to summarise")
    slope, icept = fits["slope"].to_numpy(), fits["intercept"].to_numpy()
    lo, hi = bootstrap_ci(slope, np.mean, rng=rng)
    return {
        "n_sessions": int(len(fits)),
        "slope_mean": float(np.mean(slope)),
        "slope_sem": sem(slope),
        "slope_ci_lo": lo,
        "slope_ci_hi": hi,
        "intercept_mean": float(np.mean(icept)),
        "intercept_sem": sem(icept),
        "r2_median": float(np.median(fits["r2"])),
    }


def run_pipeline(paths: Optional[Paths] = None, *, overwrite: bool = False,
                 verbose: bool = True) -> tuple[pd.DataFrame, dict]:
    """
    Orchestrator: ensure data exists, fit, save, summarise.

    The ONLY function in this module allowed to touch io/ or print. Keeping it
    at the bottom of the file means everything above stays unit-testable.
    """
    _io.make_fake_dataset(paths, overwrite=overwrite)
    raw = _io.load_raw(paths)
    fits = fit_per_session(raw)
    out = _io.save_processed(fits, RESULTS_NAME, paths)
    summary = summarize_sessions(fits)
    if verbose:
        print(f"fitted {summary['n_sessions']} sessions "
              f"({fits.attrs.get('n_skipped', 0)} skipped) -> {out}")
        print(f"  slope {summary['slope_mean']:.3f} "
              f"[{summary['slope_ci_lo']:.3f}, {summary['slope_ci_hi']:.3f}] "
              f"| median r2 {summary['r2_median']:.3f}")
    return fits, summary
