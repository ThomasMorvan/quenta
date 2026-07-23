"""
Synthetic demo dataset: per-session linear data, written to <raw>/ as CSV.
Paths come in as arguments, DataFrames go out.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..settings import Paths, get_settings

__all__ = ["DATASET_NAME", "raw_path", "make_fake_dataset", "load_raw",
           "save_processed", "load_processed"]

DATASET_NAME = "demo_sessions.csv"


def _paths(paths: Optional[Paths]) -> Paths:
    """Convenience only: notebooks may omit paths, library code
    should pass it."""
    return paths if paths is not None else get_settings().paths


def raw_path(paths: Optional[Paths] = None, name: str = DATASET_NAME) -> Path:
    return _paths(paths).raw / name


def make_fake_dataset(paths: Optional[Paths] = None, *,
                      config: Optional[dict] = None,
                      overwrite: bool = False) -> Path:
    """
    Generate the synthetic dataset and write it to <raw>/demo_sessions.csv.

    Each session has its own slope and intercept, jittered around the group
    values, so there is genuine between-session variance to analyse.

    config : dict like settings.demo. Defaults to get_settings().demo.
    Returns the path written (or the existing path if overwrite=False).
    """
    p = _paths(paths)
    cfg = dict(config if config is not None else get_settings().demo)
    out = raw_path(p)
    if out.exists() and not overwrite:
        return out

    rng = np.random.default_rng(int(cfg["seed"]))
    n_sessions, n_trials = int(cfg["n_sessions"]), int(cfg["n_trials"])
    rows = []
    for s in range(n_sessions):
        b0 = float(cfg["intercept"]) + rng.normal(0, 0.4)
        b1 = float(cfg["slope"]) + rng.normal(0, 0.25)
        x = rng.uniform(float(cfg["x_lo"]), float(cfg["x_hi"]), n_trials)
        y = b0 + b1 * x + rng.normal(0, float(cfg["noise_sd"]), n_trials)
        rows.append(pd.DataFrame({"session": s, "trial": np.arange(n_trials),
                                  "x": x, "y": y,
                                  "true_intercept": b0, "true_slope": b1}))

    df = pd.concat(rows, ignore_index=True)
    p.ensure()
    df.to_csv(out, index=False)
    return out


def load_raw(paths: Optional[Paths] = None,
             name: str = DATASET_NAME) -> pd.DataFrame:
    """
    Load the raw dataset.

    Columns: session (int), trial (int), x (float), y (float),
             true_intercept, true_slope (floats; ground truth, demo only).
    """
    path = raw_path(paths, name)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found: Run io.make_fake_dataset() first, or point "
            f"settings at the right data_root (current: {_paths(paths).root})")
    return pd.read_csv(path)


def save_processed(df: pd.DataFrame, name: str,
                   paths: Optional[Paths] = None) -> Path:
    """Write a derived table to <processed>/<name>.csv."""
    p = _paths(paths)
    p.ensure()
    out = p.processed / (name if name.endswith(".csv") else f"{name}.csv")
    df.to_csv(out, index=False)
    return out


def load_processed(name: str, paths: Optional[Paths] = None) -> pd.DataFrame:
    p = _paths(paths)
    path = p.processed / (name if name.endswith(".csv") else f"{name}.csv")
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run analysis step first.")
    return pd.read_csv(path)
