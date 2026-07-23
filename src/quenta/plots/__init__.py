"""plots: DataFrame in, Figure out.

DO
- take already-computed DataFrames as arguments
- return a matplotlib Figure (and accept an `ax=` so panels compose)
- call utils.plotting for styling and saving
- keep one function per figure panel, so a paper figure is an assembly

DON'T
- load data (the caller does that, via io/)
- compute statistics: if a plot needs a fit, it takes the fit as an
  argument, so no recompute
- call plt.show() inside a function
- hardcode an output path
"""

from ..utils._reexport import export_modules

__all__ = export_modules(__path__, __name__, globals())
