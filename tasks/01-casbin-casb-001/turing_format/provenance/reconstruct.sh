#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm it
# matches the recorded base tree exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/casbin/pycasbin.git"
UPSTREAM_COMMIT="f858158e85eb9abdf308fd356d0246b89922b11b"   # v2.8.0
BASE_COMMIT="780c97f6bf13c00c46df685eb9954616ce4672b8"
BASE_TREE="ad95d0a744fac86d80a48c2b627170b1e3640262"
COMMIT_MSG="Add PolicyAdminEnforcer stub, policy administration doc, and utility tests (feature unimplemented)"

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
