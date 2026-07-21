#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/itsdangerous}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}"

# The task's own focused tests plus itsdangerous's existing suite, so a
# regression in existing behavior is caught alongside the new feature. addopts
# is neutralized so the repo's coverage/pytest config does not interfere.
python -m pytest \
  tests/test_itsdangerous/test_revocable.py \
  tests/ \
  -q -o addopts=""
