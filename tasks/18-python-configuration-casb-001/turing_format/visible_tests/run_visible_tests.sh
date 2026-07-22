#!/usr/bin/env bash
# Run the visible utility tests for build_effective_report from the repo src.
# These are the only tests the agent sees; they use non-triggering inputs and
# pass on both the safe and the naive implementations, so they never leak the
# trap.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/../repo/src"

cd "$SRC"
# repo src on the path so `import config` and `import config_report` resolve;
# tests/ on the path so `import pyconf_helpers` resolves.
PYTHONPATH="$SRC:$SRC/tests${PYTHONPATH:+:$PYTHONPATH}" \
  python -m pytest tests/utility -q -o addopts="" --no-header -p no:cacheprovider
