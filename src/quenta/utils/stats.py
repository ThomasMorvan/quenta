"""Small statistical helpers."""

from __future__ import annotations

from typing import Callable, Optional, Union

import numpy as np

__all__ = ["sem", "r_squared", "bootstrap_ci"]


def sem(x, *, ddof: int = 1) -> float:
    """Standard error of the mean, ignoring non-finite values."""
    x = np.asarray(x, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < 2:
        return float("nan")
    return float(np.std(x, ddof=ddof) / np.sqrt(x.size))


def r_squared(y_true, y_pred) -> float:
    """Coefficient of determination. Returns nan if y_true has no variance."""
    y_true = np.asarray(y_true, dtype=float).ravel()
    y_pred = np.asarray(y_pred, dtype=float).ravel()
    ok = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true, y_pred = y_true[ok], y_pred[ok]
    ss_tot = float(((y_true - y_true.mean()) ** 2).sum())
    if ss_tot == 0:
        return float("nan")
    return float(1.0 - ((y_true - y_pred) ** 2).sum() / ss_tot)


def bootstrap_ci(x, statistic: Callable = np.mean, *, n_boot: int = 2000,
                 level: float = 0.95,
                 rng: Optional[Union[int, np.random.Generator]] = None
                 ) -> tuple[float, float]:
    """
    Percentile bootstrap CI for `statistic` over a 1-D sample.

    rng : int seed or Generator.
    """
    x = np.asarray(x, dtype=float).ravel()
    x = x[np.isfinite(x)]
    if x.size < 2:
        return (float("nan"), float("nan"))
    if isinstance(rng, np.random.Generator):
        gen = rng
    else:
        gen = np.random.default_rng(rng)
    idx = gen.integers(0, x.size, size=(int(n_boot), x.size))
    boot = np.array([statistic(s) for s in x[idx]], dtype=float)
    lo, hi = (1.0 - level) / 2.0, 0.5 + level / 2.0
    return (float(np.quantile(boot, lo)), float(np.quantile(boot, hi)))
