#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm the
# reconstructed tree and commit match the recorded values exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/zopefoundation/RestrictedPython.git"
UPSTREAM_COMMIT="aff96dd7e425de1288eb3737f3b20d2a8de4bb28"   # tag 8.4
BASE_TREE="99291a7b035688c1b1a81715f78bb61116d98605"
BASE_COMMIT="70da1e6b16b4307f038a4670aa2b2bc306bc08b0"
COMMIT_MSG="Add routing-rule stub, ticket, and visible tests (feature unimplemented)"

# Fixed identity + dates so the scaffolding commit hash is reproducible.
export GIT_AUTHOR_NAME="Task Author"
export GIT_AUTHOR_EMAIL="author@example.com"
export GIT_COMMITTER_NAME="Task Author"
export GIT_COMMITTER_EMAIL="author@example.com"
export GIT_AUTHOR_DATE="2026-08-01T00:00:00 +0000"
export GIT_COMMITTER_DATE="2026-08-01T00:00:00 +0000"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

git clone --quiet --config core.autocrlf=false --config core.eol=lf "$UPSTREAM_URL" "$WORK/app"
cd "$WORK/app"
git -c advice.detachedHead=false checkout --quiet "$UPSTREAM_COMMIT"
git config core.autocrlf false
git config core.eol lf

git apply "$HERE/baseline.patch"
git add -A
git -c commit.gpgsign=false commit --quiet -m "$COMMIT_MSG"

RECON_TREE="$(git rev-parse 'HEAD^{tree}')"
RECON_COMMIT="$(git rev-parse HEAD)"
echo "recorded base tree:        $BASE_TREE"
echo "reconstructed base tree:   $RECON_TREE"
echo "recorded base commit:      $BASE_COMMIT"
echo "reconstructed base commit: $RECON_COMMIT"
if [ "$RECON_TREE" != "$BASE_TREE" ]; then
  echo "MISMATCH: reconstructed base tree differs from recorded base tree." >&2
  exit 1
fi
if [ "$RECON_COMMIT" != "$BASE_COMMIT" ]; then
  echo "MISMATCH: reconstructed base commit differs from recorded base commit." >&2
  exit 1
fi
echo "OK: reconstructed base tree and commit match."
