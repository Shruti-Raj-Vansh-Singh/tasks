#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/structlog}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}"

# The task's own focused tests plus structlog's renderer suite, so a regression
# in existing behavior is caught alongside the new feature.
python -m pytest \
  tests/test_audit.py \
  tests/processors/test_renderers.py \
  -q -o addopts="" -p no:cacheprovider
