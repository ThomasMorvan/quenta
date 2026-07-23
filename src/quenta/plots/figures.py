"""Figures for the demo pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..settings import Paths
from ..utils.plotting import despine, label_axes, save_figure

__all__ = ["plot_session_lines", "plot_slope_distribution", "figure_overview",
           "save_overview"]


def plot_session_lines(raw: pd.DataFrame, fits: pd.DataFrame, *, ax=None,
                       max_points: int = 400, rng: int = 0):
    """Scatter of the raw data with one fitted line per session overlaid."""
    if ax is None:
        _, ax = plt.subplots(figsize=(5.2, 4.0))

    show = (raw.sample(max_points, random_state=rng)
            if len(raw) > max_points else raw)
    ax.scatter(show["x"], show["y"], s=8, alpha=0.25, color="0.5",
               linewidths=0, label="trials", zorder=1)

    xx = np.linspace(raw["x"].min(), raw["x"].max(), 100)
    cmap = plt.get_cmap("viridis")
    for i, r in fits.reset_index(drop=True).iterrows():
        ax.plot(xx, r["intercept"] + r["slope"] * xx, lw=1.3,
                color=cmap(i / max(len(fits) - 1, 1)), alpha=0.9, zorder=2)

    label_axes(ax, xlabel="x", ylabel="y",
               title=f"{len(fits)} session fits")
    ax.legend(fontsize=8, loc="upper left")
    return despine(ax)


def plot_slope_distribution(fits: pd.DataFrame,
                            summary: Optional[dict] = None, *,
                            ax=None):
    """Per-session slopes with their CIs; group mean/CI from `summary`."""
    if ax is None:
        _, ax = plt.subplots(figsize=(5.2, 4.0))

    f = fits.sort_values("slope").reset_index(drop=True)
    y = np.arange(len(f))
    ax.hlines(y, f["slope_lo"], f["slope_hi"], color="0.7", lw=1.5, zorder=1)
    ax.plot(f["slope"], y, "o", ms=5, color="C0", zorder=2, label="session")

    if summary is not None:
        ax.axvline(summary["slope_mean"], color="C3", lw=1.6, zorder=3,
                   label="group mean")
        ax.axvspan(summary["slope_ci_lo"], summary["slope_ci_hi"],
                   color="C3", alpha=0.15, zorder=0, label="95% CI")

    ax.set_yticks(y)
    ax.set_yticklabels(f["session"].astype(int), fontsize=7)
    label_axes(ax, xlabel="slope", ylabel="session", title="slope by session")
    ax.legend(fontsize=8, loc="lower right")
    return despine(ax)


def figure_overview(raw: pd.DataFrame, fits: pd.DataFrame,
                    summary: Optional[dict] = None):
    """Assemble the panels into one figure.
    Returns the Figure and saves nothing."""
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
    plot_session_lines(raw, fits, ax=axes[0])
    plot_slope_distribution(fits, summary, ax=axes[1])
    fig.tight_layout()
    return fig


def save_overview(fig, paths: Paths, name: str = "overview",
                  formats=("png", "pdf")) -> list[Path]:
    """Save into <figures>/. Path resolution stays with the caller's Paths."""
    return save_figure(fig, paths.figures / f"{name}.png", formats=formats)
