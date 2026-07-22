#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/urllib3}"
cd "$REPO_DIR"
export PYTHONPATH="$REPO_DIR/src:${PYTHONPATH:-}"

# The task's own visible tests. They live in a top-level webhook_tests/ dir
# (not urllib3's test/) because test/conftest.py imports optional dev deps
# (trustme, hypercorn dummyserver) at collection time; keeping the visible suite
# separate lets it run with only pytest installed.
python -m pytest \
  webhook_tests/test_webhook.py \
  -q -o addopts="" -p no:cacheprovider
