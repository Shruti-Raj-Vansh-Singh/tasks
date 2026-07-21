#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="${REPO_UNDER_TEST:-/workspace/bottle}"
cd "$REPO_DIR"
PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}" python -m pytest test/test_idempotency.py -q
