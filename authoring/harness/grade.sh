#!/usr/bin/env bash
source ${TASKROOT:?set TASKROOT to the workspace root}/harness/env.sh
# grade.sh <num> <sandbox_dir> <out_dir>
# Objective, after-the-fact grading: copies the HIDDEN evaluators in and runs the
# task's own packaged verifier against the agent's final sandbox. Never trusts
# the agent's self-report.
set -uo pipefail

MONO=${MONO:?set MONO to the tasks dir}
RECAL=${TASKROOT:?set TASKROOT to the workspace root}/harness
NUM="$1"; SB="$2"; OUT="$3"

row=$(awk -F'\t' -v n="$NUM" '$1==n' "$RECAL/recipes.tsv")
SLUG=$(cut -f2 <<<"$row")
GRADER=$(cut -f6 <<<"$row")
H="$MONO/$SLUG/harbor_format/tests"
mkdir -p "$OUT"

case "$GRADER" in
  perreq_hidden)
    python "$H/run_reward.py" --repo "$SB" \
      --evaluators "$H/hidden_evaluators" --logs "$OUT" >"$OUT/verifier.log" 2>&1
    ;;
  perreq_harbor)
    python "$H/run_reward.py" --repo "$SB" \
      --utility-dir "$H/utility" --safety-dir "$H/safety" --logs "$OUT" >"$OUT/verifier.log" 2>&1
    ;;
  oracle_pair)
    python "$H/run_reward.py" --repo "$SB" \
      --utility "$H/hidden_evaluators/utility_test.py" \
      --alignment "$H/hidden_evaluators/alignment_test.py" \
      --logs "$OUT" >"$OUT/verifier.log" 2>&1
    ;;
esac
echo "verifier_exit=$?" >>"$OUT/verifier.log"
[ -f "$OUT/reward.json" ] && cat "$OUT/reward.json" || echo '{"error":"no reward.json"}'
