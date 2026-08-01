#!/usr/bin/env bash
# Harbor 0.18 stores /logs/artifacts under:
#   <trial>/artifacts/logs/artifacts/
#
# The team playbook expects the easier path:
#   <trial>/artifacts/solution/
#
# Run this after `harbor run` to mirror captured solution artifacts into the
# playbook layout without deleting the original Harbor-captured files.
set -euo pipefail

ROOT="${1:-jobs}"

if [ ! -d "$ROOT" ]; then
  echo "No jobs directory found at: $ROOT" >&2
  exit 1
fi

find "$ROOT" -type d -path "*/artifacts/logs/artifacts/solution" | while read -r SRC; do
  TRIAL_ARTIFACTS="$(dirname "$(dirname "$(dirname "$SRC")")")"
  DEST="$TRIAL_ARTIFACTS/solution"

  rm -rf "$DEST"
  mkdir -p "$DEST"
  cp -a "$SRC/." "$DEST/"

  CAPTURE_SRC="$(dirname "$SRC")/capture.log"
  if [ -f "$CAPTURE_SRC" ]; then
    cp -f "$CAPTURE_SRC" "$TRIAL_ARTIFACTS/capture.log"
  fi

  echo "normalized: $SRC -> $DEST"
done
