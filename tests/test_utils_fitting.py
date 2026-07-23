"""Tests for utils.fitting."""

from __future__ import annotations

import numpy as np
import pytest

from quenta.utils.fitting import LineFit, fit_line, predict


@pytest.fixture
def line_data():
    rng = np.random.default_rng(42)
    x = rng.uniform(-3, 3, 500)
    return x, 2.0 + 1.5 * x + rng.normal(0, 0.5, 500)


def test_agrees_with_polyfit_exactly(line_data):
    """Analytic cross-check: same estimator, so agreement should be small."""
    small = 1e-10
    x, y = line_data
    slope, intercept = np.polyfit(x, y, 1)
    f = fit_line(x, y)
    assert f.slope == pytest.approx(slope, abs=small)
    assert f.intercept == pytest.approx(intercept, abs=small)


def test_recovers_known_parameters(line_data):
    """Statistical claim, so the tolerance is loose and tied to sample size."""
    x, y = line_data
    f = fit_line(x, y)
    assert f.slope == pytest.approx(1.5, abs=0.1)
    assert f.intercept == pytest.approx(2.0, abs=0.1)
    assert 0.9 < f.r2 <= 1.0
    assert f.n == 500


def test_noiseless_data_is_exact():
    x = np.linspace(-5, 5, 50)
    f = fit_line(x, 3.0 - 2.0 * x)
    assert f.slope == pytest.approx(-2.0, abs=1e-12)
    assert f.r2 == pytest.approx(1.0, abs=1e-12)


def test_ci_covers_truth_at_roughly_the_nominal_rate():
    """Coverage check: ~95% of intervals should contain the true slope. Seeded,
    and the bound is loose enough not to flake."""
    rng = np.random.default_rng(7)
    hits = 0
    for _ in range(200):
        x = rng.uniform(-3, 3, 60)
        y = 1.0 + 0.8 * x + rng.normal(0, 1.0, 60)
        lo, hi = fit_line(x, y).slope_ci(0.95)
        hits += lo <= 0.8 <= hi
    assert 0.88 <= hits / 200 <= 1.0, f"coverage {hits/200:.2f} is off nominal"


def test_non_finite_pairs_are_dropped():
    x = np.array([0.0, 1.0, 2.0, np.nan, 4.0])
    y = np.array([0.0, 2.0, 4.0, 1.0, np.inf])
    f = fit_line(x, y)
    assert f.n == 3
    assert f.slope == pytest.approx(2.0, abs=1e-12)


def test_weights_shift_the_fit_toward_the_weighted_points():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = np.array([0.0, 1.0, 2.0, 10.0])  # +outlier
    plain = fit_line(x, y).slope
    downweighted = fit_line(x, y,
                            weights=np.array([1.0, 1.0, 1.0, 1e-6])).slope
    assert downweighted < plain
    assert downweighted == pytest.approx(1.0, abs=1e-3)


@pytest.mark.parametrize("x, y, msg",
                         [([1.0], [1.0], "finite points"),
                          ([1.0, 1.0, 1.0], [1.0, 2.0, 3.0], "zero variance"),
                          ([1.0, 2.0], [1.0, 2.0, 3.0], "same shape")])
def test_bad_input_raises_instead_of_returning_nan(x, y, msg):
    """A silent nan can propagate into a figure but not an exception."""
    with pytest.raises(ValueError, match=msg):
        fit_line(x, y)


def test_ci_is_nan_when_there_are_too_few_points_for_one():
    """Two points fit exactly; there is no residual dof, so no interval."""
    f = fit_line([0.0, 1.0], [0.0, 2.0])
    assert f.n == 2
    assert all(np.isnan(b) for b in f.slope_ci())
    assert np.allclose(f.theta, [0.0, 2.0])


def test_predict_round_trips():
    x = np.linspace(0, 10, 20)
    f = fit_line(x, 1.0 + 0.5 * x)
    assert np.allclose(predict(f, x), 1.0 + 0.5 * x, atol=1e-10)


def test_result_is_immutable_and_serialisable():
    f = fit_line([0.0, 1.0, 2.0], [0.0, 1.0, 2.0])
    with pytest.raises(Exception):
        f.slope = 99.0
    assert set(f.as_dict()) >= {"intercept", "slope", "r2", "n"}
    assert isinstance(f, LineFit)
