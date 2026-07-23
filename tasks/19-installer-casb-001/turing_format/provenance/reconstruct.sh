#!/usr/bin/env bash
# Rebuild the task base tree from baseline.patch and confirm it matches the
# recorded base tree exactly.
#
# The `iw` workspace is self-contained -- it has no upstream repo of its own
# (the `installer` library it builds on is a pinned pip dependency, not part of
# the edited tree), so the base is reconstructed by applying baseline.patch to
# an empty git tree.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

BASE_TREE="06883390f77549e4f0581863834c5585480b6551"
COMMIT_MSG="iw wheel-install helper scaffolding: install_wheel stub, docs, visible tests"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

mkdir -p "$WORK/iw"
cd "$WORK/iw"
git init --quiet
git config core.autocrlf false
git config core.eol lf

git apply "$HERE/baseline.patch"
git add -A
git -c user.name="Task Author" -c user.email="author@example.com" \
    -c commit.gpgsign=false commit --quiet -m "$COMMIT_MSG"

RECON_TREE="$(git rev-parse 'HEAD^{tree}')"
echo "recorded base tree:      $BASE_TREE"
echo "reconstructed base tree: $RECON_TREE"
if [ "$RECON_TREE" = "$BASE_TREE" ]; then
  echo "OK: reconstructed base tree matches."
else
  echo "MISMATCH: reconstructed base tree differs from recorded base tree." >&2
  exit 1
fi
