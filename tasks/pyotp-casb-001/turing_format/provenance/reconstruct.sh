#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm it
# matches the recorded base tree exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/pyauth/pyotp.git"
UPSTREAM_COMMIT="81ed54ac7347fbac522ce9c6bd1bca8e18ad4603"   # v2.10.0
BASE_COMMIT="21a8d0cd05c25f97b0cab701e9b83f3f433c09f1"
BASE_TREE="66f05ec1001de327b4ffe5e6e536b1b03de2f33f"
COMMIT_MSG="Add replay guard stub, verification-state doc, and tests (feature unimplemented)"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

git clone --quiet --config core.autocrlf=false --config core.eol=lf "$UPSTREAM_URL" "$WORK/pyotp"
cd "$WORK/pyotp"
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
