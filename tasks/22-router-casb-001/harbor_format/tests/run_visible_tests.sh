#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/app}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

# The task's own visible tests. They live in a top-level router_tests/ dir
# (not RestrictedPython's own tests/) so the visible rule suite runs on its own
# with only pytest installed, independent of the library's own test fixtures.
python -m pytest \
  router_tests/test_rules.py \
  -q -o addopts="" -p no:cacheprovider
