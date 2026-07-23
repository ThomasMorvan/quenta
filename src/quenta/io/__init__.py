"""
io: the only layer that touches the filesystem.

DO
- read and write files (raw, processed, cache)
- accept a `Paths` object as an argument; default to get_settings().paths
  only in the convenience wrappers, never deep inside
- return tidy DataFrames with documented columns
- be idempotent: loading twice gives the same thing

DON'T
- compute statistics or fit anything (that's analysis/)
- plot (that's plots/)
- hardcode a path (that's what Paths is for)
- silently regenerate data that already exists (require overwrite=True)
"""

from ..utils._reexport import export_modules

__all__ = export_modules(__path__, __name__, globals())
