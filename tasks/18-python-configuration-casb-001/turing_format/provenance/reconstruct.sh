#!/usr/bin/env bash
# Rebuild the task base commit from a fresh upstream clone and confirm it
# matches the recorded base tree exactly.
#
# Usage: bash reconstruct.sh [workdir]
set -euo pipefail

UPSTREAM_URL="https://github.com/tr11/python-configuration.git"
UPSTREAM_COMMIT="75137c6f476c52f4232abd447962665a12ab7aee"   # tag 0.12.1
# The scaffolding commit's TREE is the reproducible invariant checked below; the
# commit hash depends on author/commit dates, so those are pinned here to make
# the commit hash reproducible as well.
PRISTINE_TREE="79411dd7622636ef0d0f881fcb949fdcd9e71ced"
PRISTINE_COMMIT="7faaf0303bd7c1d8ebe56763a36596c73d78734a"
BASE_TREE="550a748517ba52cb8a2134c1f1292ac5f9d8cb88"
BASE_COMMIT="b1716134bd38e9de4b67d150c3766a0ab7b0bb61"
PRISTINE_MSG="python-configuration 0.12.1 (pristine)"
BASE_MSG="Add build_effective_report stub, layered-configuration doc, and visible utility tests (feature unimplemented)"
COMMIT_DATE="2026-07-22T00:00:00 +0000"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-$(mktemp -d)}"

# 1. Clone upstream at the pinned 0.12.1 commit (LF-only, no autocrlf mangling).
git clone --quiet --config core.autocrlf=false --config core.eol=lf "$UPSTREAM_URL" "$WORK/upstream"
git -C "$WORK/upstream" -c advice.detachedHead=false checkout --quiet "$UPSTREAM_COMMIT"

# 2. Lay out the pristine package the way the task ships it: the importable
#    `config` package is upstream's `src/config`, plus the setuptools-scm
#    `_version.py` (which upstream generates at build time and does not track in
#    git). The pinned _version.py is carried alongside this script.
BUILD="$WORK/build"
rm -rf "$BUILD"; mkdir -p "$BUILD"
git -C "$BUILD" init -q
git -C "$BUILD" config core.autocrlf false
git -C "$BUILD" config core.eol lf
git -C "$BUILD" config user.name "Task Author"
git -C "$BUILD" config user.email "author@example.com"
git -C "$BUILD" config commit.gpgsign false

cp -r "$WORK/upstream/src/config" "$BUILD/config"
# Upstream ships a config/.gitignore that excludes the setuptools-scm _version.py
# (and __pycache__); the packaged tree carries the pinned _version.py instead and
# does not ship that ignore file. Drop it so the tree matches the recorded hash.
rm -f "$BUILD/config/.gitignore"
cp "$HERE/_version.py" "$BUILD/config/_version.py"

git -C "$BUILD" add -A
GIT_AUTHOR_DATE="$COMMIT_DATE" GIT_COMMITTER_DATE="$COMMIT_DATE" \
    git -C "$BUILD" commit --quiet -m "$PRISTINE_MSG"
RECON_PRISTINE_TREE="$(git -C "$BUILD" rev-parse 'HEAD^{tree}')"

# 3. Apply the scaffolding (baseline.patch adds the feature stub, the doc, and
#    the visible utility tests -- feature unimplemented) and commit the base.
git -C "$BUILD" apply "$HERE/baseline.patch"
git -C "$BUILD" add -A
GIT_AUTHOR_DATE="$COMMIT_DATE" GIT_COMMITTER_DATE="$COMMIT_DATE" \
    git -C "$BUILD" commit --quiet -m "$BASE_MSG"
RECON_BASE_TREE="$(git -C "$BUILD" rev-parse 'HEAD^{tree}')"

echo "recorded pristine tree:      $PRISTINE_TREE"
echo "reconstructed pristine tree: $RECON_PRISTINE_TREE"
echo "recorded base tree:          $BASE_TREE"
echo "reconstructed base tree:     $RECON_BASE_TREE"

ok=1
if [ "$RECON_PRISTINE_TREE" != "$PRISTINE_TREE" ]; then
  echo "MISMATCH: reconstructed pristine tree differs." >&2; ok=0
fi
if [ "$RECON_BASE_TREE" != "$BASE_TREE" ]; then
  echo "MISMATCH: reconstructed base tree differs." >&2; ok=0
fi
if [ "$ok" = 1 ]; then
  echo "OK: reconstructed pristine and base trees match."
else
  exit 1
fi
