"""Shared test stuff.
Every test that touches disk gets its own tmp data_root, so no
test accidentally ever read or write in the real data directory."""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest

from quenta.settings import load_settings

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    add_opts_help = "option to use each test's slow test parameters " \
                    "instead of quick checks ones (e.g. iteration counts)."
    parser.addoption("--slow", action="store_true", default=False,
                     help=add_opts_help)


@pytest.fixture
def slow(request):
    """True when --slow is passed, so tests can also use the slow parameters
    instead of the quick ones."""
    return request.config.getoption("--slow")


@pytest.fixture
def settings(tmp_path):
    """Settings rooted in tmp_path, with directories created."""
    s = load_settings(config_dir=REPO_ROOT, data_root=tmp_path / "data")
    s.paths.ensure()
    return s


@pytest.fixture
def paths(settings):
    return settings.paths


@pytest.fixture
def toy_sessions():
    """Hand-made tidy frame: 3 sessions, known slopes, no disk involved."""
    rng = np.random.default_rng(0)
    frames = []
    for s, (b0, b1) in enumerate([(1.0, 2.0), (0.0, -1.0), (2.0, 0.5)]):
        x = rng.uniform(-3, 3, 80)
        frames.append(pd.DataFrame({"session": s, "trial": np.arange(80),
                                    "x": x,
                                    "y": b0 + b1 * x + rng.normal(0, 0.2, 80),
                                    "true_intercept": b0, "true_slope": b1}))
    return pd.concat(frames, ignore_index=True)
