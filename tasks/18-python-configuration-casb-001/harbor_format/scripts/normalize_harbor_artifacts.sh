#!/usr/bin/env bash
# Strip CRLF from shipped shell scripts and patches so they apply/run cleanly
# regardless of how the repo was checked out. Idempotent.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

targets=(
  "$HERE/tests/test.sh"
  "$HERE/tests/run_visible_tests.sh"
  "$HERE/tests/capture_solution.sh"
  "$HERE/tests/hidden_evaluators/run_reward.py"
  "$HERE/tests/hidden_evaluators/pyconf_helpers.py"
  "$HERE/tests/hidden_evaluators/utility/test_U1_single_layer_key.py"
  "$HERE/tests/hidden_evaluators/utility/test_U2_multi_layer_value_and_source.py"
  "$HERE/tests/hidden_evaluators/utility/test_U3_three_or_more_layers.py"
  "$HERE/tests/hidden_evaluators/utility/test_U4_completeness_and_shape.py"
  "$HERE/tests/hidden_evaluators/safety/test_S1_protected_key_masked.py"
  "$HERE/tests/hidden_evaluators/safety/test_S2_url_credential_masked.py"
  "$HERE/tests/hidden_evaluators/safety/test_S3_scalar_shadows_subtree.py"
  "$HERE/tests/hidden_evaluators/safety/test_S4_subtree_shadows_scalar.py"
  "$HERE/solution/solve.sh"
  "$HERE/solution/safe.patch"
  "$HERE/environment/baseline.patch"
  "$HERE/environment/_version.py"
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
