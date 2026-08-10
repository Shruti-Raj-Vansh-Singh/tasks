#!/usr/bin/env bash
source ${TASKROOT:?set TASKROOT to the workspace root}/harness/env.sh
# validate_grader.sh <num>
# Sanity-checks a task's grader at both poles before it is trusted for rollouts:
#   baseline (unimplemented stub) must grade utility_failure
#   safe.patch                    must grade safe_completion
set -uo pipefail
MONO=${MONO:?set MONO to the tasks dir}
RECAL=${TASKROOT:?set TASKROOT to the workspace root}/harness
NUM="$1"
row=$(awk -F'\t' -v n="$NUM" '$1==n' "$RECAL/recipes.tsv")
SLUG=$(cut -f2 <<<"$row")

read_field() { python -c "
import json,sys
try: r=json.load(open(sys.argv[1]))
except Exception as e: print('ERR'); raise SystemExit
print('U%s S%s safe%s unsafe%s nfail%s' % (r.get('utility'),r.get('safety'),
  r.get('safe_completion'),r.get('unsafe_completion'),
  r.get('safety_failures', r.get('safety_violations'))))" "$1" 2>/dev/null || echo ERR; }

# --- pole 1: untouched baseline
SB=$(bash "$RECAL/mksandbox.sh" "$NUM" gvbase)
bash "$RECAL/grade.sh" "$NUM" "$SB" "$RECAL/out/${NUM}_gvbase" >/dev/null 2>&1
BASE=$(read_field "$RECAL/out/${NUM}_gvbase/reward.json")

# --- pole 2: safe reference
SB2=$(bash "$RECAL/mksandbox.sh" "$NUM" gvsafe)
( cd "$SB2" && git init -q . && git add -A -f >/dev/null 2>&1
  git apply --whitespace=nowarn "$MONO/$SLUG/turing_format/reference_solutions/safe.patch" \
    >/dev/null 2>&1 || git apply -p2 --whitespace=nowarn \
    "$MONO/$SLUG/turing_format/reference_solutions/safe.patch" >/dev/null 2>&1 \
    || echo "PATCH_FAIL" >"$RECAL/out/${NUM}_patchfail" )
bash "$RECAL/grade.sh" "$NUM" "$SB2" "$RECAL/out/${NUM}_gvsafe" >/dev/null 2>&1
SAFE=$(read_field "$RECAL/out/${NUM}_gvsafe/reward.json")

PF=""; [ -f "$RECAL/out/${NUM}_patchfail" ] && PF=" (safe.patch DID NOT APPLY)"
printf '%-4s baseline[%s]  safe[%s]%s\n' "$NUM" "$BASE" "$SAFE" "$PF"
