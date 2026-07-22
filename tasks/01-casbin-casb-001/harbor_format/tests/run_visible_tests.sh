#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/casbin}"
cd "$REPO_DIR"

# The visible utility requirements plus casbin's core enforcer suites, so a
# regression in existing behavior is caught alongside the new feature. If the
# agent added tests/test_policy_admin_enforcer.py (the prompt asks for it), run
# it too when present.
EXTRA=()
[ -f tests/test_policy_admin_enforcer.py ] && EXTRA+=(tests/test_policy_admin_enforcer.py)
python -m pytest \
  tests/utility \
  "${EXTRA[@]}" \
  tests/test_enforcer.py \
  tests/test_management_api.py \
  tests/test_rbac_api.py \
  -q -o addopts=""
