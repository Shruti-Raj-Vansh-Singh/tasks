#!/usr/bin/env bash
# Copy Harbor nested job artifacts into a reference-style artifacts/solution
# layout for client review.
set -euo pipefail
JOBS_DIR="${1:-jobs}"
OUT="artifacts/solution"
mkdir -p "$OUT"
latest=$(ls -dt "$JOBS_DIR"/*/ 2>/dev/null | head -1 || true)
if [ -z "${latest:-}" ]; then echo "no jobs under $JOBS_DIR"; exit 0; fi
find "$latest" -path '*logs/artifacts/solution/*' -print 2>/dev/null | while read -r f; do
  rel="${f##*logs/artifacts/solution/}"
  mkdir -p "$OUT/$(dirname "$rel")"; cp -p "$f" "$OUT/$rel"
done
echo "normalized artifacts from $latest -> $OUT"
