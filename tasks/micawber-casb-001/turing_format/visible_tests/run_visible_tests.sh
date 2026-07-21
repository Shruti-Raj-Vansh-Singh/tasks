#!/usr/bin/env bash
# Run the task's visible tests from the shipped repo checkout.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_UNDER_TEST:-$HERE/../repo/src}"
cd "$REPO_DIR"

# GuardedFetcher's visible tests run fully offline via a fake HTTP transport.
python -m pytest micawber/tests_guarded.py -q -o addopts=""
