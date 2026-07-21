#!/usr/bin/env bash
# Capture the final repository state into /logs/artifacts/solution so Harbor
# stores the patch, changed-file list, and browsable changed files with the run.
#
# - oracle run: captures the applied safe reference patch
# - model run:  captures the agent's final code changes
#
# The verifier calls this before copying hidden tests into the checkout, so the
# captured diff contains only the solution under evaluation.
set -u

REPO_DIR="${REPO_UNDER_TEST:-/workspace/itsdangerous}"
OUT=/logs/artifacts/solution

mkdir -p "$OUT/changed"
cd "$REPO_DIR" 2>/dev/null || { echo "[capture] repo missing at $REPO_DIR"; exit 0; }

BASE=$(git rev-parse HEAD 2>/dev/null || true)
echo "${BASE:-unknown}" > "$OUT/base_commit.txt"

git add -A 2>/dev/null || true

git diff --cached --binary > "$OUT/agent.patch" 2>/dev/null || true
git diff --cached --name-status > "$OUT/changed_files.txt" 2>/dev/null || true
git diff --cached --stat > "$OUT/changed_files.stat.txt" 2>/dev/null || true

while IFS= read -r -d '' file_path; do
  if [ -f "$file_path" ]; then
    mkdir -p "$OUT/changed/$(dirname "$file_path")"
    cp -p "$file_path" "$OUT/changed/$file_path"
  fi
done < <(git diff --cached --name-only -z 2>/dev/null)

changed_count=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
echo "[capture] repo=$REPO_DIR base=${BASE:-unknown} changed_files=${changed_count} -> $OUT"
