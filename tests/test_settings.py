"""Test settings resolution order. Cheap test to catch stupid mistakes
like wrong data_root.

Every test passes an explicit `config_dir` (not the real cwd) so the
suite can never depend on (or disturb) actual settings files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quenta.settings import load_settings

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_defaults_work_with_no_config_at_all(tmp_path):
    """An installed package with no settings.toml must still function."""
    s = load_settings(config_dir=tmp_path)
    assert s.paths.root.is_absolute()
    assert s.sources == ("defaults",)
    assert s.demo["n_sessions"] > 0


def test_committed_settings_are_read():
    s = load_settings(config_dir=REPO_ROOT)
    assert any("settings.toml" in src for src in s.sources)


def test_local_file_overrides_committed(tmp_path):
    (tmp_path / "settings.toml").write_text(
        '[paths]\ndata_root = "/from/committed"\n[demo]\nn_sessions = 8\n')
    (tmp_path / "settings.local.toml").write_text(
        '[paths]\ndata_root = "/from/local"\n')
    s = load_settings(config_dir=tmp_path)
    assert s.paths.root == Path("/from/local")
    assert s.demo["n_sessions"] == 8


def test_explicit_argument_beats_everything(tmp_path):
    (tmp_path / "settings.local.toml").write_text(
        '[paths]\ndata_root = "/from/local"\n')
    s = load_settings(config_dir=tmp_path, data_root="/from/arg")
    assert s.paths.root == Path("/from/arg")


def test_subdirs_hang_off_the_root(tmp_path):
    s = load_settings(config_dir=REPO_ROOT, data_root=tmp_path)
    for p in (s.paths.raw, s.paths.processed, s.paths.figures, s.paths.cache):
        assert p.parent == s.paths.root


def test_ensure_creates_directories(tmp_path):
    s = load_settings(config_dir=REPO_ROOT, data_root=tmp_path / "new")
    assert not s.paths.root.exists()
    s.paths.ensure()
    assert all(p.is_dir() for p in s.paths.as_dict().values())


def test_with_root_rebases_and_keeps_subdir_names(tmp_path):
    s = load_settings(config_dir=REPO_ROOT, data_root="/a")
    t = s.with_root(tmp_path)
    assert t.paths.root == tmp_path.resolve()
    assert t.paths.raw.name == s.paths.raw.name


def test_settings_are_frozen(tmp_path):
    s = load_settings(config_dir=REPO_ROOT, data_root=tmp_path)
    with pytest.raises(Exception):
        s.paths.root = Path("/somewhere/else")


def test_committed_settings_have_no_personal_path():
    """Guard against the classic mistake of committing settings.local.toml
    content into settings.toml."""
    text = (REPO_ROOT / "settings.toml").read_text()
    for needle in ("/home/", "/Users/", "C:\\", "/media/", "/mnt/"):
        assert needle not in text, (
            f"settings.toml contains a machine-specific path ({needle!r}); "
            f"put it in settings.local.toml instead")


def test_local_settings_file_is_gitignored():
    assert "settings.local.toml" in (REPO_ROOT / ".gitignore").read_text()
