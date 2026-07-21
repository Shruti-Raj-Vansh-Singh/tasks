#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/stream-unzip}"
cd "$REPO_DIR"

# The task's own focused tests for the extract-to-dir helper. stream-unzip's own
# suite (test.py) is slow (sleep/property-based) and exercises the async
# interface; it is not run here because the feature does not touch it. The
# verifier's utility/alignment oracles are what gate U and S.
python -m pytest \
  test_extract.py \
  -q -o addopts=""
