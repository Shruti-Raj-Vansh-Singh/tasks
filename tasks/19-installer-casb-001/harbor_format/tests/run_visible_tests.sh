#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/iw}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

# The task's own visible tests. They live in a top-level iw_tests/ dir and run
# on their own with only pytest + the installer library installed.
python -m pytest \
  iw_tests/test_install.py \
  -q -o addopts="" -p no:cacheprovider
