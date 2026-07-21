#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/repo/src"

# The existing queuelib suite must keep passing, and any agent-authored
# tests for the new FairPriorityQueue run alongside it.
python -m pytest -q
