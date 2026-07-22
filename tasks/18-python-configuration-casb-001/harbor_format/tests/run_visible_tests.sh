#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/pyconf}"
cd "$REPO_DIR/src"
export PYTHONPATH="$REPO_DIR/src:$REPO_DIR:${PYTHONPATH:-}"

# The task's visible utility tests for build_effective_report. These are the
# tests an agent is expected to make pass; they run fully offline (each builds a
# ConfigurationSet in-process from plain dicts) and never touch the network. The
# hidden safety tests are not present in the checkout and are added by the
# verifier afterward.
python -m pytest \
  tests/utility \
  -q -o addopts=""
