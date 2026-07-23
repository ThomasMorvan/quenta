"""
utils: standalone, copy-pasteable helpers.

THE ONE RULE: every module in here must run when copied, alone, into an
unrelated project. Third-party imports (numpy, scipy, matplotlib) are fine.
Imports from anywhere else in `quenta` are not allowed.

DO
 - take plain arrays / DataFrames / paths as ARGUMENTS
 - keep each module self-contained, even at the cost of a little duplication
 - carry a provenance header so a pasted copy can be traced back
 - stay deterministic: take a seed or a Generator, never touch global state

DON'T
    - import quenta.settings, or read a config file, or know a path default
    - import a sibling utils module (fitting.py must not import stats.py)
    - load or save data as a side effect
    - print; raise or return instead

`tests/test_layering.py` enforces the first two DON'Ts by AST-parsing every
module here AND by copying each one to a temp dir and importing it clean.
Only this __init__ may import siblings, since a pasted copy never takes it.
"""

from ._reexport import export_modules

__all__ = export_modules(__path__, __name__, globals())
