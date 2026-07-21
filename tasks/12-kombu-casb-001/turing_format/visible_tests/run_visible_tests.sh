#!/usr/bin/env bash
# Run the task's visible tests from the shipped repo checkout.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${REPO_UNDER_TEST:-$HERE/../repo/src}"
cd "$REPO_DIR"

# decompress_bounded's visible tests run fully offline with in-memory payloads.
python -m pytest t/unit/test_safe_compression.py -q -o addopts=""
