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

```bash
git clone <url> && cd quenta
pip install -e ".[dev]"        # or: uv pip install -e ".[dev]"
```

If some other project depends on `quenta` (e.g. the repo for a paper), install
it there pinned to a specific tag, instead of the latest commit:

```bash
pip install "quenta @ git+ssh://git@github.com/ThomasMorvan/quenta@v0.1.0"
```

It's a good idea to use tags (permanent pointer to one commit) for anything that produced a figure in a paper or when we have a major change, so we can easily get the exact same code later to regenerate if something goes wrong (change function default params, etc.).

--> Bump `version` in `pyproject.toml` and tag the commit:

```bash
git tag v0.1.1 && git push --tags
```

Note: Never move a tag that's already been pushed. Retagging silently changes what
`v0.1.1` means for anyone who installed it before the change, which is bad. If a release needs fixing, tag `v0.1.2` instead.

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
