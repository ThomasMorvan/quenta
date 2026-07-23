"""Test repo structure, maybe overkill.

Check `utils/` is copy-pasteable: each module has to run when dropped, alone,
into an unrelated project and check that the arrow points one
way: no layer should import a layer above it."""

from __future__ import annotations

import ast
import importlib
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

PKG = "quenta"
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src" / PKG
UTILS = SRC / "utils"
UTIL_MODULES = sorted(p for p in UTILS.glob("*.py") if p.name != "__init__.py")

# A layer may only import the layers listed for it:
ALLOWED = {
    "utils": set(),
    "settings": set(),
    "io": {"settings", "utils"},
    "analysis": {"settings", "utils", "io"},
    "plots": {"settings", "utils", "io"},
}


def _imports_in(source: str, path: Path):
    """Yield (module, lineno, level) for every import in `source`. `path` is
    only used for error messages, so it need not exist on disk."""
    tree = ast.parse(source, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield a.name, node.lineno, 0
        elif isinstance(node, ast.ImportFrom):
            yield (node.module or ""), node.lineno, node.level


def _raw_imports(path: Path):
    """Yield (module, lineno, level) for every import statement in the file."""
    return _imports_in(path.read_text(), path)


def _package_parts(path: Path) -> list[str]:
    """Dotted package containing `path`, e.g. ['quenta', 'analysis']."""
    rel = path.relative_to(SRC.parent)  # quenta/analysis/x.py
    parts = list(rel.parts)
    return parts[:-1]


def _resolve(path: Path, mod: str, level: int) -> str | None:
    """Absolute module name for an import as written in `path`, or None."""
    if level == 0:
        return mod or None
    pkg = _package_parts(path)
    base = pkg[: len(pkg) - (level - 1)] if level > 1 else pkg
    return ".".join([*base, *(mod.split(".") if mod else [])]) or None


def _in_package_layer(abs_mod: str | None) -> str | None:
    """'quenta.io.datasets' -> 'io'.  Non-quenta imports -> None."""
    if not abs_mod:
        return None
    parts = abs_mod.split(".")
    return parts[1] if parts[0] == PKG and len(parts) > 1 else None


def test_utils_modules_exist():
    assert UTIL_MODULES, "no utils modules found, did the layout change?"


@pytest.mark.parametrize("path", UTIL_MODULES, ids=lambda p: p.name)
def test_utils_module_has_no_internal_imports(path):
    """No relative imports and no `quenta.*` imports, anywhere in the file."""
    bad = []
    for mod, lineno, level in _raw_imports(path):
        if level > 0:
            bad.append(f"{path.name}:{lineno} relative import (level {level}) "
                       f"of {mod!r}")
        elif mod == PKG or mod.startswith(f"{PKG}."):
            bad.append(f"{path.name}:{lineno} imports {mod!r}")
    assert not bad, ("utils modules must be standalone (copy-pasteable):\n  "
                     + "\n  ".join(bad))


@pytest.mark.parametrize("path", UTIL_MODULES, ids=lambda p: p.name)
def test_utils_module_never_mentions_settings(path):
    """Paths and config arrive as arguments; utils must not know about them."""
    src = path.read_text()
    for needle in ("get_settings", "QUENTA_", "settings.toml"):
        assert needle not in src, (
            f"{path.name} mentions {needle!r}; utils takes paths as arguments")


@pytest.mark.parametrize("path", UTIL_MODULES, ids=lambda p: p.name)
def test_utils_module_imports_standalone_in_clean_dir(path, tmp_path):
    """
    The real copy-paste test: copy the file out, import it in an isolated
    interpreter (-I: no user site, no cwd on sys.path) from a directory that
    knows nothing about this repo.
    """
    dest = tmp_path / path.name
    shutil.copy(path, dest)
    code = textwrap.dedent(f"""
        import sys
        sys.path.insert(0, ".")
        mod = __import__("{path.stem}")
        assert getattr(mod, "__all__", None), "module should export __all__"
        for name in mod.__all__:
            assert hasattr(mod, name), f"__all__ lists missing {{name!r}}"
        print("ok", len(mod.__all__))
    """)
    proc = subprocess.run(
        [sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True,
        text=True, env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path),
                        "MPLBACKEND": "Agg"})
    assert proc.returncode == 0, (
        f"{path.name} does not import standalone:\n{proc.stderr}")


def test_utils_init_only_imports_siblings():
    """__init__ may wire the subpackage together to discover siblings
    dynamically, or a level-1 relative import of an actual sibling file,
    but never a module from another layer, statically or otherwise."""
    for mod, lineno, level in _raw_imports(UTILS / "__init__.py"):
        if level == 0:
            assert mod != PKG and not mod.startswith(f"{PKG}."), (
                f"utils/__init__.py:{lineno} imports {mod!r}, not stdlib")
            continue
        assert level == 1, (f"utils/__init__.py:{lineno} import of {mod!r} "
                            f"must be a level-1 relative import")
        _str = f"utils/__init__.py:{lineno} import of {mod!r} " \
               f"must be a sibling module"
        assert (UTILS / f"{mod}.py").is_file(), (_str)


@pytest.mark.parametrize("layer", sorted(ALLOWED))
def test_layer_import_direction(layer):
    """A layer may only import layers listed as below it."""
    as_module = SRC / f"{layer}.py"
    if as_module.is_file():
        files = [as_module]
    else:
        files = sorted((SRC / layer).rglob("*.py"))
    assert files, f"layer {layer!r} has no files"

    violations = []
    for f in files:
        for mod, lineno, level in _raw_imports(f):
            other = _in_package_layer(_resolve(f, mod, level))
            if other and other != layer and other not in ALLOWED[layer]:
                _str = f"{f.relative_to(SRC)}:{lineno}" \
                       f"{layer!r} imports {other!r}"
                violations.append(_str)
    assert not violations, ("import direction must point down:\n  "
                            + "\n  ".join(violations))


def test_direction_check_actually_catches_a_violation():
    """A deliberately bad file must be flagged. Without this,
    a broken resolver would make every direction test vacuously pass.

    The bad file is never written: `_resolve` only needs the path to work out
    which package it would sit in, so a path that doesn't exist is enough."""
    bad = SRC / "utils" / "_tmp_violation.py"
    source = "from ..settings import get_settings\n"
    found = [_in_package_layer(_resolve(bad, mod, level))
             for mod, _, level in _imports_in(source, bad)]
    _str = f"resolver failed to see the violation: {found}"
    assert "settings" in found, _str


SUBPACKAGES = ["analysis", "io", "plots", "utils"]


def _leaf_modules():
    """Public leaf modules: anything not private, matching what
    export_modules() itself treats as a module."""
    for pkg in SUBPACKAGES:
        for path in sorted((SRC / pkg).glob("*.py")):
            if not path.stem.startswith("_"):
                yield path, f"{PKG}.{pkg}.{path.stem}"


LEAF_MODULES = list(_leaf_modules())


def _public_top_level_defs(path: Path) -> set[str]:
    """Top-level function/class names that aren't private. Deliberately
    ignores nested defs and plain constants."""
    tree = ast.parse(path.read_text(), filename=str(path))
    return {node.name for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef))
            and not node.name.startswith("_")}


@pytest.mark.parametrize("path,dotted", LEAF_MODULES,
                         ids=[d for _, d in LEAF_MODULES])
def test_every_public_def_is_exported(path, dotted):
    """A def/class missing from __all__ is unreachable via the subpackage's
    dynamic re-export with no error so catch that here instead."""
    module = importlib.import_module(dotted)
    missing = _public_top_level_defs(path) - set(module.__all__)
    _str = f"{path.name} defines {sorted(missing)} but missing from __all__"
    assert not missing, _str


@pytest.mark.parametrize("pkg", SUBPACKAGES)
def test_subpackage_reexports_every_module(pkg):
    """A module the subpackage's __init__.py fails to pick up (e.g. it
    isn't a valid Python module, or discovery silently misses it) would make
    its functions unreachable via `quenta.<pkg>` with no error, so catch that
    here instead, rather than relying on __init__.py being correct."""
    package = importlib.import_module(f"{PKG}.{pkg}")
    expected = set()
    for path, dotted in LEAF_MODULES:
        if dotted.startswith(f"{PKG}.{pkg}."):
            expected |= set(importlib.import_module(dotted).__all__)
    expec_str = f"no leaf modules found for {pkg!r}. Did the layout change?"
    assert expected, expec_str
    missing = expected - set(package.__all__)
    missing_str = f"quenta.{pkg} does not re-export {sorted(missing)} " \
                  f"from its leaf modules"
    assert not missing, missing_str
