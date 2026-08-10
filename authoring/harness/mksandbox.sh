#!/usr/bin/env bash
source ${TASKROOT:?set TASKROOT to the workspace root}/harness/env.sh
# mksandbox.sh <num> <run_tag>
# Builds an isolated blind sandbox for one task rollout OUTSIDE the task package.
# Strips .git, hidden evaluators, reference solutions, calibration, scoring,
# provenance, and any safety-named test so the agent cannot read the answer.
set -euo pipefail

MONO=${MONO:?set MONO to the tasks dir}
RECAL=${TASKROOT:?set TASKROOT to the workspace root}/harness
NUM="$1"; TAG="$2"

row=$(awk -F'\t' -v n="$NUM" '$1==n' "$RECAL/recipes.tsv")
[ -n "$row" ] || { echo "no recipe for $NUM" >&2; exit 1; }
SLUG=$(cut -f2 <<<"$row")
SRC=$(cut -f3 <<<"$row")
PROMPT=$(cut -f4 <<<"$row")

SB="$RECAL/sb/${NUM}_${TAG}"
rm -rf "$SB"; mkdir -p "$SB"
cp -r "$MONO/$SLUG/turing_format/$SRC/." "$SB/"

# --- blind the sandbox -------------------------------------------------------
find "$SB" -name .git -prune -exec rm -rf {} + 2>/dev/null || true
find "$SB" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find "$SB" -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
for leak in hidden_evaluators reference_solutions calibration scoring provenance runs review_notes.md test_metadata.json point.md task_card.md; do
  find "$SB" -name "$leak" -prune -exec rm -rf {} + 2>/dev/null || true
done
# any test file whose name advertises a safety requirement
find "$SB" -type f \( -name "test_S[0-9]*.py" -o -name "*alignment*test*.py" -o -name "*safety*.py" \) -delete 2>/dev/null || true
find "$SB" -type d -name safety -prune -exec rm -rf {} + 2>/dev/null || true

cp "$MONO/$SLUG/$PROMPT" "$SB/TASK_PROMPT.md"
echo "$SB"
