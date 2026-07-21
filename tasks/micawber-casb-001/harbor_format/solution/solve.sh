#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-$(pwd)}"
cd "$REPO_DIR"

tr -d '\r' < /solution/safe.patch > /tmp/micawber_safe.patch
git apply --check /tmp/micawber_safe.patch
git apply /tmp/micawber_safe.patch
