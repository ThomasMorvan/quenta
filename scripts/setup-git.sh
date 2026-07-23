#!/usr/bin/env bash
# One-time setup: registers the local git filters this repo relies on.
# Run this once to define filters (here, stop tracking notebook metadata).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

git config filter.strip-notebook-metadata.clean 'python3 scripts/nb_strip_metadata.py'
echo "configured: filter.strip-notebook-metadata.clean"
