"""
Machine configuration: paths and project defaults.

This is the ONLY module that knows where files live on a given computer.
Everything downstream receives paths as arguments.

DO
- resolve data_root / raw / processed / figures / cache
- hold project-level defaults (sample sizes, seeds, thresholds)
- expose everything as a frozen Settings object

DON'T
- import anything else from quenta (this sits just above utils)
- read or write data files (that's io/)
- hardcode a personal path in the committed settings.toml
- get imported by utils/

Resolution order (highest priority first):
1. an explicit `data_root=` argument :: tests / one-off reruns
2. settings.local.toml :: your machine, gitignored
3. settings.toml :: committed defaults
4. DEFAULTS below :: so an installed package still works
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

__all__ = ["Paths", "Settings", "load_settings", "get_settings",
           "reload_settings", "find_config_dir"]

CONFIG_NAME = "settings.toml"
LOCAL_NAME = "settings.local.toml"

DEFAULTS: dict[str, Any] = {
            "paths": {"data_root": "~/.local/share/quenta",
                      "raw": "raw",
                      "processed": "processed",
                      "figures": "figures",
                      "cache": "cache"},
            "demo": {"n_sessions": 8, "n_trials": 120, "seed": 42,
                     "intercept": 2.0, "slope": 1.5, "noise_sd": 1.0,
                     "x_lo": -3.0, "x_hi": 3.0}}


# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Paths:
    """Resolved absolute directories. Pass these down; never re-derive them."""
    root: Path
    raw: Path
    processed: Path
    figures: Path
    cache: Path

    def ensure(self) -> "Paths":
        """Create every directory. Call once at the start of a pipeline."""
        for p in (self.root, self.raw, self.processed,
                  self.figures, self.cache):
            p.mkdir(parents=True, exist_ok=True)
        return self

    def as_dict(self) -> dict[str, Path]:
        return {"root": self.root, "raw": self.raw,
                "processed": self.processed,
                "figures": self.figures, "cache": self.cache}


@dataclass(frozen=True)
class Settings:
    paths: Paths
    demo: dict[str, Any] = field(default_factory=dict)
    sources: tuple[str, ...] = ()

    def with_root(self, root) -> "Settings":
        """Return a copy rooted elsewhere. Used by tests and one-off reruns."""
        return replace(self, paths=_build_paths(Path(root).expanduser(),
                                                _subdir_names(self.paths)))


def _subdir_names(paths: Paths) -> dict[str, str]:
    return {k: p.name for k, p in paths.as_dict().items() if k != "root"}


def _build_paths(root: Path, subdirs: dict[str, str]) -> Paths:
    root = Path(root).expanduser().resolve()
    return Paths(root=root, **{k: root / v for k, v in subdirs.items()})


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        out[k] = _deep_merge(out[k], v) if isinstance(v, dict) and isinstance(
            out.get(k), dict) else v
    return out


def _read_toml(path: Path) -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def find_config_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from `start` (default: cwd) looking for settings.toml, then try
    the repo root relative to this file (works for `pip install -e .`)."""
    start = Path(start or Path.cwd()).resolve()
    for d in (start, *start.parents):
        if (d / CONFIG_NAME).is_file():
            return d
    repo_root = Path(__file__).resolve().parents[2]     # src/quenta/ -> repo
    return repo_root if (repo_root / CONFIG_NAME).is_file() else None


def load_settings(config_dir=None, *, data_root=None) -> Settings:
    """
    Build a Settings object. An explicit argument beats the local file, which
    beats the committed file, which beats the built-in defaults.

    config_dir : where to look for settings.toml / settings.local.toml.
    data_root  : force the data root (tests use this with a tmp_path).
    """
    cfg, sources = dict(DEFAULTS), ["defaults"]

    d = Path(config_dir) if config_dir else find_config_dir()
    if d is not None:
        for name in (CONFIG_NAME, LOCAL_NAME):
            if (d / name).is_file():
                cfg = _deep_merge(cfg, _read_toml(d / name))
                sources.append(str(d / name))

    paths_cfg = dict(cfg["paths"])
    root = paths_cfg.pop("data_root")
    if data_root:
        root = data_root
        sources.append("data_root=<argument>")

    return Settings(paths=_build_paths(Path(root), paths_cfg),
                    demo=dict(cfg.get("demo", {})), sources=tuple(sources))


_CACHE: Optional[Settings] = None


def get_settings() -> Settings:
    """Cached settings for interactive/notebook use. Library code should take
    `paths` as an argument instead of calling this."""
    global _CACHE
    if _CACHE is None:
        _CACHE = load_settings()
    return _CACHE


def reload_settings() -> Settings:
    """Drop the cache and re-read from disk (after
    editing settings.local.toml)."""
    global _CACHE
    _CACHE = None
    return get_settings()
