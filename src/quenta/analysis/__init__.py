"""
analysis: DataFrame in, numbers out.

DO
- transform tidy data into tidy results (one row per unit of analysis)
- call utils/ for the actual maths
- return DataFrames/dicts; let the caller decide whether to save them
- keep every function testable with a hand-made DataFrame and no disk

DON'T
- plot anything
- read or write files inside the computation
- print progress, except in the orchestrator
- reimplement maths that belongs in utils/
"""

from ..utils._reexport import export_modules

__all__ = export_modules(__path__, __name__, globals())
