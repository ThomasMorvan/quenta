"""Example analysis pipeline that uses functions from all submodules"""

from __future__ import annotations

import matplotlib

from quenta import io, plots
from quenta.analysis import run_pipeline
from quenta.settings import load_settings

matplotlib.use("Agg")


def pipeline() -> int:
    data_root = None  # None -> whatever the settings.toml files say
    overwrite = False
    settings = load_settings(data_root=data_root)
    paths = settings.paths.ensure()
    print(f"data_root: {paths.root}\n"
          f"settings from: {', '.join(settings.sources)}")

    fits, summary = run_pipeline(paths, overwrite=overwrite)
    raw = io.load_raw(paths)
    fig = plots.figure_overview(raw, fits, summary)
    written = plots.save_overview(fig, paths)
    print("figures: " + ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    pipeline()
