#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="${REPO_UNDER_TEST:-/workspace/peewee}"
cd "$REPO_DIR"
PYTHONPATH="$REPO_DIR${PYTHONPATH:+:$PYTHONPATH}" python -m pytest tests/test_record_sync.py -q
