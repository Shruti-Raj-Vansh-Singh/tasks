#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/micawber}"
cd "$REPO_DIR"

# The task's own focused tests for GuardedFetcher. These are the visible tests
# an agent is expected to make pass; they run fully offline via a fake HTTP
# transport and never touch the real network. micawber's broader suite
# (providers/parsers/django) is unaffected by this feature and is not re-run
# here.
python -m pytest \
  micawber/tests_guarded.py \
  -q -o addopts=""
