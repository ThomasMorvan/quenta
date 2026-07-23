"""
End-to-end pipeline check, runnable headless:  python -m quenta.verify
(also installed as the `quenta-verify` console script)

Runs the same calls a notebook would, minus the prose, against synthetic
data, so a broken install, a broken layer, or a rotted notebook all fail
here first.
"""

from __future__ import annotations

import argparse

import matplotlib

from . import io, plots
from .analysis import run_pipeline
from .settings import load_settings


def main(argv=None) -> int:
    # inside main: this module is imported by `import quenta`, and forcing a
    # backend at import time would break plt.show() for every other caller
    matplotlib.use("Agg")
    ap = argparse.ArgumentParser(
        description="Run the quenta verification pipeline.")
    ap.add_argument("--data-root", default=None,
                    help="override settings data_root")
    ap.add_argument("--overwrite", action="store_true",
                    help="regenerate the raw dataset even if it exists")
    args = ap.parse_args(argv)

    settings = load_settings(data_root=args.data_root)
    paths = settings.paths.ensure()
    print(f"data_root: {paths.root}\n"
          f"settings from: {', '.join(settings.sources)}")

    fits, summary = run_pipeline(paths, overwrite=args.overwrite)
    raw = io.load_raw(paths)
    fig = plots.figure_overview(raw, fits, summary)
    written = plots.save_overview(fig, paths)
    print("figures: " + ", ".join(str(p) for p in written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
