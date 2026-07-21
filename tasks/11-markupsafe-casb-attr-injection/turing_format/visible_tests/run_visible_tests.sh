#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/repo/src"
PYTHONPATH="$ROOT/repo/src" python -m pytest tests -q
