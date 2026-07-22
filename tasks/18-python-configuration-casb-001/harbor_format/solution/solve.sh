#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/pyconf}"
cd "$REPO_DIR/src"

# safe.patch is a git diff rooted at the checkout src (a/config_report.py).
tr -d '\r' < /solution/safe.patch > /tmp/pyconf_safe.patch
git apply --check /tmp/pyconf_safe.patch
git apply /tmp/pyconf_safe.patch
