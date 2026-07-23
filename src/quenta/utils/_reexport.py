"""
Discover sibling module modules by directory listing and re-export
whatever each declares in its own __all__, so a new file/function
needs no manual wiring anywhere."""

from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules

__all__ = ["export_modules"]


def export_modules(path, package: str, namespace: dict, *,
                   skip_packages: bool = False,
                   skip: tuple[str, ...] = ()) -> list[str]:
    """
    Import every direct, non-private submodule of `package` (whose __path__
    is `path`), copy the names in its __all__ into `namespace` (call with
    globals()), and return the merged names for the caller's own __all__.

    skip : module names to leave alone, for entry points that are meant to be
           run (`python -m ...`) rather than imported.
    """
    exported: list[str] = []
    for info in sorted(iter_modules(path), key=lambda m: m.name):
        if (info.name.startswith("_") or info.name in skip
                or (skip_packages and info.ispkg)):
            continue
        module = import_module(f".{info.name}", package)
        module_all = getattr(module, "__all__", None)
        if not module_all:
            continue
        namespace.update({name: getattr(module, name) for name in module_all})
        exported += module_all
    return exported
