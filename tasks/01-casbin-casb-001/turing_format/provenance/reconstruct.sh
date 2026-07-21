#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm it
# matches the recorded base tree exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/casbin/pycasbin.git"
UPSTREAM_COMMIT="f858158e85eb9abdf308fd356d0246b89922b11b"   # v2.8.0
BASE_COMMIT="6279b3d91c3d1c9a2cdbc9539e1b0bb8143cd18b"
BASE_TREE="21da682d7b32558b51b646891c9c9b0910d557f8"
COMMIT_MSG="Add cached enforcer stub, policy consistency doc, and tests (feature unimplemented)"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

git clone --quiet --config core.autocrlf=false --config core.eol=lf "$UPSTREAM_URL" "$WORK/casbin"
cd "$WORK/casbin"
git -c advice.detachedHead=false checkout --quiet "$UPSTREAM_COMMIT"
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
