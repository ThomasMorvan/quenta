"""Example least-squares line fitting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats as _sps

__all__ = ["LineFit", "fit_line", "predict"]


@dataclass(frozen=True)
class LineFit:
    """Result of fit_line. `n` is the number of points actually used."""
    intercept: float
    slope: float
    r2: float
    intercept_se: float
    slope_se: float
    n: int

    @property
    def theta(self) -> np.ndarray:
        return np.array([self.intercept, self.slope])

    def slope_ci(self, level: float = 0.95) -> tuple[float, float]:
        """Two-sided t interval for the slope."""
        if self.n <= 2:
            return (np.nan, np.nan)
        crit = _sps.t.ppf(0.5 + level / 2.0, df=self.n - 2)
        return (self.slope - crit * self.slope_se,
                self.slope + crit * self.slope_se)

    def as_dict(self) -> dict:
        return {"intercept": self.intercept,
                "slope": self.slope, "r2": self.r2,
                "intercept_se": self.intercept_se, "slope_se": self.slope_se,
                "n": self.n}


def fit_line(x, y, *, weights: Optional[np.ndarray] = None) -> LineFit:
    """
    Fit y = intercept + slope * x by (weighted) least squares.

    Non-finite pairs are dropped. Raises ValueError on fewer than 2 usable
    points or on zero variance in x, rather than returning a silent nan.
    """
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    if x.shape != y.shape:
        raise ValueError(
            f"x and y must have the same shape, got {x.shape} {y.shape}")

    ok = np.isfinite(x) & np.isfinite(y)
    if weights is not None:
        weights = np.asarray(weights, dtype=float).ravel()
        ok &= np.isfinite(weights) & (weights > 0)
    x, y = x[ok], y[ok]
    w = None if weights is None else weights[ok]

    n = x.size
    if n < 2:
        raise ValueError(f"need >= 2 finite points, got {n}")
    if np.ptp(x) == 0:
        raise ValueError("x has zero variance; slope is undefined")

    X = np.column_stack([np.ones(n), x])
    if w is None:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        dof = max(n - 2, 1)
        s2 = float(resid @ resid) / dof
        cov = s2 * np.linalg.inv(X.T @ X)
        ss_res = float(resid @ resid)
        ss_tot = float(((y - y.mean()) ** 2).sum())
    else:
        sw = np.sqrt(w)
        beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
        resid = y - X @ beta
        dof = max(n - 2, 1)
        s2 = float((w * resid ** 2).sum()) / dof
        cov = s2 * np.linalg.inv((X * w[:, None]).T @ X)
        ybar = float((w * y).sum() / w.sum())
        ss_res = float((w * resid ** 2).sum())
        ss_tot = float((w * (y - ybar) ** 2).sum())

    se = np.sqrt(np.diag(cov))
    return LineFit(intercept=float(beta[0]), slope=float(beta[1]),
                   r2=float(1.0 - ss_res / ss_tot) if ss_tot > 0 else np.nan,
                   intercept_se=float(se[0]), slope_se=float(se[1]), n=int(n))


def predict(fit: LineFit, x) -> np.ndarray:
    """Evaluate the fitted line at x."""
    x = np.asarray(x, dtype=float)
    return fit.intercept + fit.slope * x
