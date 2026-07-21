#!/usr/bin/env bash
# Add a task folder under tasks/ with a parallel-safe sequence number.
#
#   bash tasks/add_task.sh /path/to/local/<slug> [--slug <name>]
#
# Run from inside a clone of the tasks monorepo. The source directory is the
# task tree to add; its basename (minus any leading NN- prefix) is the slug
# unless --slug is given. See tasks/NUMBERING.md for the protocol.
set -euo pipefail

SRC="${1:-}"
if [ -z "$SRC" ] || [ ! -d "$SRC" ]; then
  echo "usage: bash tasks/add_task.sh /path/to/local/<slug> [--slug <name>]" >&2
  exit 2
fi
shift || true

SLUG=""
if [ "${1:-}" = "--slug" ]; then SLUG="${2:-}"; fi
if [ -z "$SLUG" ]; then
  SLUG="$(basename "$SRC")"
  SLUG="${SLUG#[0-9][0-9]-}"   # drop any existing NN- prefix
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
REG="tasks/REGISTRY.tsv"

# Stage a clean copy once; the loop only moves this into place.
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
cp -r "$SRC" "$STAGE/$SLUG"
find "$STAGE/$SLUG" \( -name .git -o -name __pycache__ -o -name '*.egg-info' \
  -o -name '.pytest_cache' \) -exec rm -rf {} + 2>/dev/null || true

next_num() {  # highest num in registry + 1, zero-padded to 2
  local max
  max="$(awk -F'\t' 'NR>1 && $1 ~ /^[0-9]+$/ {n=$1+0; if (n>m) m=n} END{print m+0}' "$REG")"
  printf '%02d' "$((max + 1))"
}

for attempt in 1 2 3 4 5 6 7 8; do
  git fetch --quiet origin main
  git reset --hard --quiet origin/main

  if awk -F'\t' -v s="$SLUG" 'NR>1 && $2==s {found=1} END{exit !found}' "$REG"; then
    echo "slug '$SLUG' is already in the registry; aborting." >&2
    exit 1
  fi

  NUM="$(next_num)"
  DEST="tasks/$NUM-$SLUG"
  if [ -e "$DEST" ]; then
    echo "attempt $attempt: $DEST already exists, refetching..." >&2
    continue
  fi

  cp -r "$STAGE/$SLUG" "$DEST"
  # Timestamp is passed in from the caller's environment (scripts here run in a
  # sandbox without a live clock); fall back to a marker the author backfills.
  printf '%s\t%s\t%s\t%s\n' "$NUM" "$SLUG" "${TASK_ADDED_UTC:-pending}" "pending" >> "$REG"

  git add -A
  git -c commit.gpgsign=false commit --quiet \
    -m "Add $NUM-$SLUG task (parallel-safe numbering via REGISTRY.tsv)"

  if git push --quiet origin main 2>/dev/null; then
    echo "landed as $DEST"
    exit 0
  fi

  echo "attempt $attempt: push rejected (someone landed first); renumbering..." >&2
  git reset --hard --quiet "origin/main@{0}" 2>/dev/null || git reset --hard --quiet HEAD~1
done

echo "could not land after several attempts; retry manually." >&2
exit 1
