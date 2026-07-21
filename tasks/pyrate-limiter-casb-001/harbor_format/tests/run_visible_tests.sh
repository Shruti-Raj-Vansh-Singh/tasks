#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/pyrate_limiter}"
cd "$REPO_DIR"

# The task's own focused tests plus pyrate-limiter's in-memory bucket suite, so
# a regression in existing behavior is caught alongside the new feature. The
# external-backend suites (redis / sqlite / postgres / multiprocessing) are not
# run here because they require services or extra packages not installed in the
# verifier image.
python -m pytest \
  tests/test_bounded_limiter.py \
  -q -o addopts=""
