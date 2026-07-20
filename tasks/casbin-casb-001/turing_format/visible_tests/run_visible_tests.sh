#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/repo/src"

# The task's own focused tests plus casbin's core enforcer suites, so a
# regression in existing behavior is caught alongside the new feature.
python -m pytest \
  tests/test_cached_enforcer.py \
  tests/test_enforcer.py \
  tests/test_management_api.py \
  tests/test_rbac_api.py \
  -q -o addopts=""
