#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm it
# matches the recorded base tree exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/coleifer/micawber.git"
UPSTREAM_COMMIT="46fa8e11ac7274ad6f729fea8b09d14eb63c5cf1"   # 0.7.0
# The scaffolding commit's TREE is the reproducible invariant checked below; the
# commit hash depends on author/commit dates, so it is pinned here to make the
# commit reproducible as well.
BASE_COMMIT="31cde8b2df51f8cc10315b163ef45b8ac27761b6"
BASE_TREE="c69d6f7c1a678510be9cfdc63629e1ea42673bca"
COMMIT_MSG="Add GuardedFetcher stub, network access policy doc, and visible tests (feature unimplemented)"
COMMIT_DATE="2026-07-22T00:00:00 +0000"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

git clone --quiet --config core.autocrlf=false --config core.eol=lf "$UPSTREAM_URL" "$WORK/micawber"
cd "$WORK/micawber"
git -c advice.detachedHead=false checkout --quiet "$UPSTREAM_COMMIT"
git config core.autocrlf false
git config core.eol lf

git apply "$HERE/baseline.patch"
git add -A
GIT_AUTHOR_DATE="$COMMIT_DATE" GIT_COMMITTER_DATE="$COMMIT_DATE" \
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
