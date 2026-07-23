"""Tests for utils.stats: seeded reproducibility and CI coverage."""

from __future__ import annotations

import numpy as np
import pytest

from quenta.utils.stats import bootstrap_ci, r_squared, sem


def test_sem_matches_the_formula():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert sem(x) == pytest.approx(np.std(x, ddof=1) / 2.0)


def test_sem_ignores_non_finite():
    assert sem([1.0, 2.0, np.nan, 3.0, 4.0]) == pytest.approx(
        sem([1.0, 2.0, 3.0, 4.0]))


@pytest.mark.parametrize("x", [[], [1.0]])
def test_sem_of_too_few_points_is_nan(x):
    assert np.isnan(sem(x))


def test_r_squared_bounds():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert r_squared(y, y) == pytest.approx(1.0)
    assert r_squared(y, np.full_like(y, y.mean())) == pytest.approx(0.0)
    assert np.isnan(r_squared([2.0, 2.0, 2.0], [1.0, 2.0, 3.0]))


def test_bootstrap_is_reproducible_with_a_seed():
    x = np.random.default_rng(0).normal(size=100)
    assert bootstrap_ci(x, rng=1) == bootstrap_ci(x, rng=1)
    assert bootstrap_ci(x, rng=1) != bootstrap_ci(x, rng=2)


def test_bootstrap_ci_brackets_the_sample_mean():
    x = np.random.default_rng(3).normal(loc=5.0, size=200)
    lo, hi = bootstrap_ci(x, np.mean, n_boot=1000, rng=0)
    assert lo < x.mean() < hi


def test_bootstrap_coverage_is_near_nominal(slow):
    """~95% of intervals should contain the true mean."""
    n_reps = 150 if slow else 20  # slow is more reliable, but takes longer
    lo_tol, hi_tol = (0.85, 1.0) if slow else (0.65, 1.0)
    rng = np.random.default_rng(11)
    hits = 0
    for _ in range(n_reps):
        x = rng.normal(loc=2.0, scale=1.0, size=80)
        lo, hi = bootstrap_ci(x, np.mean, n_boot=600,
                              rng=int(rng.integers(1e6)))
        hits += lo <= 2.0 <= hi
    coverage = hits / n_reps
    assert lo_tol <= coverage <= hi_tol, (
        f"coverage {coverage:.2f} is off nominal ({n_reps} reps)")
