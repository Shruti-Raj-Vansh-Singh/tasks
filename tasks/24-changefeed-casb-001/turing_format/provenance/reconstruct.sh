#!/usr/bin/env bash
# Reconstruct the changefeed-casb-001 base tree from the scaffolding patch.
#
# The `changefeed` workspace has no upstream repo of its own: it is purpose-built
# code that imports the pinned `dictdiffer` library. There is therefore no base
# *commit* on top of an upstream tag -- the base is defined entirely by its TREE
# hash, reproduced by applying baseline.patch to an EMPTY git tree.
#
# Usage: bash reconstruct.sh [DEST_DIR]
#   DEST_DIR defaults to ./_cf_recon
#
# On success it prints the reconstructed tree hash and asserts it equals the
# expected base tree.
set -euo pipefail

EXPECTED_TREE="dddc64b2e7ee164a6a6c4d409b2cd148acb10476"
COMMIT_MSG="changefeed activity-feed recorder scaffolding: record_change stub, docs, visible tests"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH="${HERE}/baseline.patch"
DEST="${1:-${HERE}/_cf_recon}/cf"

if [ ! -f "${PATCH}" ]; then
  echo "ERROR: baseline.patch not found next to this script (${PATCH})" >&2
  exit 1
fi

rm -rf "${DEST}"
mkdir -p "${DEST}"
cd "${DEST}"

git init -q
git config user.email "swastikr@lamatic.ai"
git config user.name "Swastik Rajvansh Singh"

# Apply the scaffolding patch to the empty tree, then commit.
git apply --whitespace=nowarn "${PATCH}"
git add -A
git commit -q -m "${COMMIT_MSG}"

ACTUAL_TREE="$(git rev-parse HEAD^{tree})"
echo "reconstructed tree: ${ACTUAL_TREE}"
echo "expected tree:      ${EXPECTED_TREE}"

if [ "${ACTUAL_TREE}" != "${EXPECTED_TREE}" ]; then
  echo "MISMATCH: reconstructed tree does not equal expected base tree" >&2
  exit 1
fi
echo "OK: base tree reproduced exactly."
