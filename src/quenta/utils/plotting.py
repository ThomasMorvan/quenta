"""
Matplotlib helpers: styling and saving. No project knowledge.

Standalone: matplotlib only. Takes an explicit output path, this module has
no idea where the figures directory is, and should not learn.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

import matplotlib.pyplot as plt

__all__ = ["despine", "save_figure", "label_axes"]


def despine(ax, *, sides: Iterable[str] = ("top", "right")):
    """Remove the given spines. Returns the axes, so it chains."""
    for s in sides:
        ax.spines[s].set_visible(False)
    return ax


def label_axes(ax, *, xlabel=None, ylabel=None, title=None):
    if xlabel is not None:
        ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    if title is not None:
        ax.set_title(title)
    return ax


def save_figure(fig, path: Union[str, Path], *, dpi: int = 150,
                formats: Optional[Iterable[str]] = None,
                close: bool = False) -> list[Path]:
    """
    Save `fig` to `path`, creating parent directories.

    formats : if given (e.g. ('png', 'pdf')), `path`'s suffix is replaced and
              one file per format is written.
    Returns the paths written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    targets = ([path] if not formats
               else [path.with_suffix(f".{f.lstrip('.')}") for f in formats])
    for t in targets:
        fig.savefig(t, dpi=dpi, bbox_inches="tight", facecolor="white")
    if close:
        plt.close(fig)
    return targets
