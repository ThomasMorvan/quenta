#!/usr/bin/env bash
# One-time setup: creates the venv and installs notebook deps and
# print steps to select the kernel in VS Code.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -m venv .venv
.venv/bin/pip install -e ".[dev]" jupyter ipykernel

cat <<'EOF'

venv ready. One manual step left, in VS Code:

  Open notebooks/demo.ipynb -> pick kernel (top-right of the notebook
  toolbar) -> Select Another Kernel... -> Python Environments... -> .venv (Python 3.x)

  If .venv isn't listed, use Enter interpreter path... and paste the full
  path to .venv/bin/python

Only need to do that once per clone.
EOF