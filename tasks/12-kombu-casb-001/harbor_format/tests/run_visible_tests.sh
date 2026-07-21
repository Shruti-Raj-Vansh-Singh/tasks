#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/kombu}"
cd "$REPO_DIR"

# The task's own focused tests for decompress_bounded. These are the visible
# tests an agent is expected to make pass; they run fully offline with in-memory
# compressed payloads and never touch a broker. kombu's broader suite is
# unaffected by this feature and is not re-run here.
python -m pytest \
  t/unit/test_safe_compression.py \
  -q -o addopts=""
