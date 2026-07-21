#!/usr/bin/env bash
# Run the task's visible tests from the shipped repo checkout.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO_UNDER_TEST:-$HERE/../repo/src}"
cd "$REPO"

PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}" python -m pytest \
  test_extract.py \
  -q -o addopts=""
