#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/unidiff}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

# The task's own visible tests. They live in a top-level patch_tests/ dir
# (not unidiff's own tests/) so the visible apply suite runs on its own with
# only pytest installed, independent of the library's parser test fixtures.
python -m pytest \
  patch_tests/test_apply.py \
  -q -o addopts="" -p no:cacheprovider
