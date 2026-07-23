# quenta
Analysis, figures, and reusable utilities for the towers evidence-accumulation
task.

## Layering

Imports should point **down** this list, never up:

```
notebooks/  # calls + prose, no logic
  plots/  # data -> Figure
  analysis/  # data -> numbers
    io/  # disk <-> data
      settings.py  # machine config, paths
        utils/  # standalone
```

## Install

Two different situations, pick the one you're in.

**You want to *use* quenta**, install with pip:

```bash
pip install quenta  # latest release
pip install quenta==0.1.0  # a specific one
```

Pin the version (`==`) for anything that produces a figure in a paper. A released version is frozen forever, so pinning is what lets you regenerate that figure years later with the exact code that made it even after defaults have changed here. Upgrade deliberately, by editing the pin.

**You want to *work on* quenta**:

```bash
git clone https://github.com/ThomasMorvan/quenta && cd quenta
pip install -e ".[dev]"  # or: uv pip install -e ".[dev]"
```

`-e` (editable) links the install to `src/quenta/` instead of copying it, so edits are live. To update afterwards, `git pull` is enough; only rerun `pip install -e ".[dev]"` when the dependencies in `pyproject.toml` change.

<details>
<summary>Installing straight from git (no PyPI)</summary>

Useful for a commit that isn't released yet, or a private fork:

```bash
pip install "quenta @ git+ssh://git@github.com/ThomasMorvan/quenta@v0.1.0"
```

Add `--force-reinstall` when updating one of these. pip compares version strings, and two different commits can both call themselves `0.1.0`, so it would otherwise decide there's nothing to do.

</details>

## Release a new version

To release a new version that can be pip installable: three steps.

**1. Bump.** Edit `version` in `pyproject.toml`, then commit it:

```bash
git commit -am "release v0.1.1"
```

**2. Tag.** This is what a `git+` install resolves:

```bash
git tag v0.1.1
git push && git push --tags
```

**3. Upload.** This is what `pip install quenta` resolves:

```bash
rm -rf dist/  # else old builds get uploaded too
python -m build  # -> dist/quenta-0.1.1.tar.gz + .whl
python -m twine check dist/*  # catches broken metadata before it's public
python -m twine upload dist/*
```

Neither a pushed tag nor an uploaded version can ever be changed (that's the point, so all 0.1.0 mean the same thing for everyone). To fix a release, bump version and go through the three steps again.

### First release from a new machine

```bash
pip install build twine
```

Get API token from https://pypi.org/manage/account/token/. Before quenta's first upload the only possible scope is "Entire account" as PyPI can't scope a token to a project that doesn't exist yet. Store token in ~/.pypirc, create, print, save and chmod:

```bash
printf '[pypi]\n  username = __token__\n  password = pypi-PASTE_IT_HERE\n' > ~/.pypirc
chmod 600 ~/.pypirc
```

The `chmod` matters: that file is a password in plain text.

To rehearse without burning a real version number (but yolo, so I did not do that), upload to https://test.pypi.org instead (`twine upload -r testpypi dist/*`, separate account and token). It doesn't reserve the name on real PyPI.

### Narrowing the token afterwards

Once a first upload exists, swap the account-wide token for a project-scoped one, so a leak can't reach your other projects. The old token works until it's deleted, so delete it *last*:

1. On the token page, "Add API token" now offers **Project: quenta**. Create
   it, copy the new `pypi-...` string.
2. Replace the `password =` line in `~/.pypirc`.
3. Now delete the account-wide token.


## Settings

Data should live **outside** the repo. Paths resolve in this order:

| priority | source | scope |
|---|---|---|
| 1 | an explicit `data_root=` argument | for tests where you need to change root |
| 2 | `settings.local.toml` | this machine, **gitignored** |
| 3 | `settings.toml` | committed defaults |
| 4 | built-in `DEFAULTS` | so an installed package still works |


```bash
cp settings.local.toml.example settings.local.toml
```

Never commit a personal path: a tracked machine-specific file means a merge
conflict every time you change device.

## Run the verification pipeline

```bash
python -m quenta.verify --data-root /path/to/data
# or open notebooks/demo.ipynb
```

Generates a synthetic per-session dataset, makes a fit and summary
at group level, and writes `overview.png/.pdf` to the figures directory.

### Notebook kernel (VS Code)

The system Python has no `pip` and no `ipykernel`, so install:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" jupyter ipykernel
```
(or just run `scripts/setup-venv.sh`, which does the same thing and prints the next step below)

Then in `notebooks/demo.ipynb`: pick kernel (top-right of the
notebook toolbar) --> **Select Another Kernel** --> **Python Environments...** -->
`.venv (Python 3.x)`. If not listed, use **Enter interpreter
path...** and paste the full path to `.venv/bin/python`.

Only need to do that once per clone.

### Commit notebooks with output, without the metadata noise
Inspired by https://gist.github.com/33eyes/431e3d432f73371509d176d0dfb95b6e
Cell outputs (figures, printed numbers) are worth committing as a record of
what the notebook produced. Kernelspec, language_info, and execution counts
are not: they're machine-specific and churn the diff every run, even when
nothing meaningful changed. A git filter strips just that, on the way in.

1. Add the filter to git config by running the following command in bash inside the repo:
```
git config filter.strip-notebook-metadata.clean 'python3 scripts/nb_strip_metadata.py'
```
   (or just run `scripts/setup-git.sh`, which does the same thing)
2. `notebooks/.gitattributes` already routes `*.ipynb` through it:
```
*.ipynb filter=strip-notebook-metadata
```

After that, commit to git as usual. Outputs stay in the committed notebook;
kernelspec/language_info/execution counts don't. Your local file on disk is
untouched either way.

To bypass the filter for one commit (e.g. you want the raw file, metadata and
all), use `git -c filter.strip-notebook-metadata.clean= add <path>` instead of
the usual `git add`.


## Tests
From an activated environment:

```bash
pytest  # everything, quick params, good for a pre-commit hook
pytest --slow  # same tests, full params for statistical confidence
pytest --cov  # which lines the tests actually run; fails under 90%
```

Coverage is opt-in rather than always-on, so a plain `pytest` stays fast. CI
runs it on the `--slow` pass. The floor exists to catch a module that stopped
being tested at all, not to chase 100%.

`if __name__ == "__main__":` blocks are excluded outright (see
`[tool.coverage.report]` in `pyproject.toml`).

From outside environment, prefix with the interpreter: `.venv/bin/python -m pytest`.

Linting is `ruff` (pycodestyle + pyflakes + import order, 79 cols; configured
in `pyproject.toml`), and CI runs it before the tests:

```bash
ruff check .  # report
ruff check . --fix  # fix what's mechanically fixable
```

Tests that pick a value from the `slow` fixture run every time, just with
reduced parameters (e.g. fewer iterations) by default and full ones under
`--slow`, instead of being skipped outright.


## The name
The two behavioral apparatuses are named **Cirith Ungol** and **Orthanc**, for together they make the *Two Towers*. The instrument of reckoning is **Amon Hen**, the Hill of the Eye, from which all things may be seen. And **Quenta** is the word in the High Speech signifying a tale or an account, as in *Quenta Silmarillion*, wherein the lore of many ages was gathered from scattered memories into a single history. Thus is this work likewise named; for out of much that was watched and set down is wrought one account, and out of that account are the figures drawn, and from those figures the tale is sung.
