#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_UNDER_TEST:-/workspace/markupsafe}"
cd "$REPO_DIR"

# The existing markupsafe suite plus any agent-authored render_attributes tests.
python -m pytest -q
