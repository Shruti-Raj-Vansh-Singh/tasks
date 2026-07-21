#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="${REPO_UNDER_TEST:-$HERE/../repo/src}"
cd "$REPO"
PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}" python -m pytest test/test_idempotency.py -q
