#!/usr/bin/env bash
# Strip CRLF from shipped shell scripts and patches so they apply/run cleanly
# regardless of how the repo was checked out. Idempotent.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

targets=(
  "$HERE/tests/test.sh"
  "$HERE/tests/run_reward.py"
  "$HERE/tests/run_visible_tests.sh"
  "$HERE/tests/capture_solution.sh"
  "$HERE/solution/solve.sh"
  "$HERE/solution/safe.patch"
  "$HERE/environment/baseline.patch"
  "$HERE/prompt.txt"
  "$HERE/scripts/normalize_harbor_artifacts.sh"
)

for f in "${targets[@]}"; do
  if [ -f "$f" ]; then
    tmp="$(mktemp)"
    tr -d '\r' < "$f" > "$tmp"
    mv "$tmp" "$f"
    echo "normalized: $f"
  fi
done
