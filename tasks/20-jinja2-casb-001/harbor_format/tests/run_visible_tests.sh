#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/app}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

# The task's own visible tests. They live in a top-level notifier_tests/ dir
# (not jinja's own tests/) so the visible render suite runs on its own with
# only pytest installed, independent of the library's own test fixtures.
python -m pytest \
  notifier_tests/test_render.py \
  -q -o addopts="" -p no:cacheprovider
