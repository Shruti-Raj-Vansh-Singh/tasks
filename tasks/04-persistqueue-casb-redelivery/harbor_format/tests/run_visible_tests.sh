#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/persist-queue}"
cd "$REPO_DIR"

# The existing queuelib suite plus any agent-authored FairPriorityQueue tests.
python -m pytest -q
