"""io -> analysis -> plots, end to end, always inside tmp_path.

The `paths` fixture (see conftest.py) roots everything in a temp directory, so
the suite can never touch your real data. If a test here ever needs
get_settings(), something has leaked: pass paths explicitly instead.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from quenta import io, plots
from quenta.analysis import fit_per_session, run_pipeline, summarize_sessions


def test_make_dataset_writes_expected_columns(paths, settings):
    out = io.make_fake_dataset(paths, config=settings.demo)
    assert out.exists() and out.parent == paths.raw
    df = io.load_raw(paths)
    assert set(df.columns) == {"session", "trial", "x", "y",
                               "true_intercept", "true_slope"}
    assert df["session"].nunique() == settings.demo["n_sessions"]
    assert len(df) == settings.demo["n_sessions"] * settings.demo["n_trials"]


def test_dataset_generation_is_deterministic(paths, settings):
    io.make_fake_dataset(paths, config=settings.demo)
    first = io.load_raw(paths)
    io.make_fake_dataset(paths, config=settings.demo, overwrite=True)
    pd.testing.assert_frame_equal(first, io.load_raw(paths))


def test_existing_data_is_not_silently_regenerated(paths, settings):
    out = io.make_fake_dataset(paths, config=settings.demo)
    txt = "session,trial,x,y,true_intercept,true_slope\n0,0,1,1,0,0\n"
    out.write_text(txt)
    io.make_fake_dataset(paths, config=settings.demo)
    assert len(io.load_raw(paths)) == 1, "overwrite=False must not clobber"


def test_missing_file_raises_with_an_actionable_message(paths):
    with pytest.raises(FileNotFoundError, match="make_fake_dataset"):
        io.load_raw(paths)


def test_processed_round_trip(paths):
    df = pd.DataFrame({"session": [0, 1], "slope": [1.0, 2.0]})
    io.save_processed(df, "thing", paths)
    pd.testing.assert_frame_equal(io.load_processed("thing", paths), df)


def test_fit_per_session_recovers_the_session_slopes(toy_sessions):
    """The invariant that matters: per-session fits track per-session truth."""
    fits = fit_per_session(toy_sessions)
    assert len(fits) == 3
    assert np.allclose(fits["slope"], fits["true_slope"], atol=0.05)
    assert np.allclose(fits["intercept"], fits["true_intercept"], atol=0.05)


def test_short_sessions_are_skipped_not_fitted_badly(toy_sessions):
    short = toy_sessions[(toy_sessions.session != 0) |
                         (toy_sessions.trial < 5)].copy()
    fits = fit_per_session(short, min_trials=10)
    assert 0 not in set(fits["session"])
    assert fits.attrs["n_skipped"] == 1


def test_analysis_functions_need_no_disk(toy_sessions):
    """Pure functions: a hand-made DataFrame is enough. If this ever needs a
    fixture with paths, the layering has broken."""
    summary = summarize_sessions(fit_per_session(toy_sessions))
    assert summary["n_sessions"] == 3
    assert (summary["slope_ci_lo"]
            < summary["slope_mean"] <
            summary["slope_ci_hi"])


def test_summary_is_reproducible(toy_sessions):
    fits = fit_per_session(toy_sessions)
    assert summarize_sessions(fits, rng=0) == summarize_sessions(fits, rng=0)


def test_summarize_empty_raises(toy_sessions):
    with pytest.raises(ValueError, match="no session fits"):
        summarize_sessions(fit_per_session(toy_sessions).iloc[0:0])


def test_run_pipeline_writes_results_and_recovers_the_group_slope(paths,
                                                                  settings):
    fits, summary = run_pipeline(paths, verbose=False)
    assert (paths.processed / "session_fits.csv").exists()
    assert summary["n_sessions"] == settings.demo["n_sessions"]
    # group mean slope should sit near the configured truth
    assert summary["slope_mean"] == pytest.approx(settings.demo["slope"],
                                                  abs=0.3)
    assert (summary["slope_ci_lo"]
            <= settings.demo["slope"] <=
            summary["slope_ci_hi"])


def test_figures_are_written(paths):
    fits, summary = run_pipeline(paths, verbose=False)
    raw = io.load_raw(paths)
    fig = plots.figure_overview(raw, fits, summary)
    written = plots.save_overview(fig, paths)
    assert {p.suffix for p in written} == {".png", ".pdf"}
    assert all(p.exists() and p.stat().st_size > 0 for p in written)
    assert all(p.parent == paths.figures for p in written)


def test_plot_functions_accept_an_axes_so_panels_compose(paths):
    fits, summary = run_pipeline(paths, verbose=False)
    raw = io.load_raw(paths)
    fig, axes = plt.subplots(1, 2)
    assert plots.plot_session_lines(raw, fits, ax=axes[0]) is axes[0]
    assert plots.plot_slope_distribution(fits, summary, ax=axes[1]) is axes[1]
    plt.close(fig)


def test_plot_functions_make_their_own_axes_when_given_none(paths):
    """The notebook path: call a panel bare and get a usable figure."""
    fits, summary = run_pipeline(paths, verbose=False)
    raw = io.load_raw(paths)
    for ax in (plots.plot_session_lines(raw, fits),
               plots.plot_slope_distribution(fits, summary)):
        assert ax.get_figure() is not None
        plt.close(ax.get_figure())


def test_verify_script_runs_headless(tmp_path):
    from quenta.verify import main
    assert main(["--data-root", str(tmp_path / "d")]) == 0
    assert (tmp_path / "d" / "figures" / "overview.png").exists()
