#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/pyotp}"
cd "$REPO_DIR"

# The task's own focused tests for the replay guard. pyotp's full legacy suite
# lives in test.py (unittest); it is run separately in the image's default CMD.
# Here we run the feature's pytest file, which is what a regression in the new
# behavior would surface in.
python -m pytest \
  tests/test_replay_guard.py \
  -q -o addopts=""
