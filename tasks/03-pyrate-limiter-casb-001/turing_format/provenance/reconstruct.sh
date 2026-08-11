#!/usr/bin/env bash
# Rebuild the task base tree and confirm it matches the recorded hash exactly.
#
# Two modes, both of which must produce the same tree:
#
#   bash reconstruct.sh [workdir]            offline - applies baseline.patch to
#                                            an empty repo. No network. This is
#                                            what the verifier image does.
#   bash reconstruct.sh --upstream [workdir] online  - clones upstream at the
#                                            recorded commit and applies
#                                            upstream_delta.patch, proving the
#                                            baseline really is upstream plus the
#                                            four scaffolding files.
set -euo pipefail

UPSTREAM_URL="https://github.com/vutran1710/PyrateLimiter.git"
UPSTREAM_COMMIT="8cb467ea54c68368eaf34deef1a6cc38c41218a2"   # v3.9.0
UPSTREAM_TREE="a30e80966ee1ab886cc7536ef35654fe4438b4d9"
BASE_COMMIT="ea8d3195a38ce1489aec0a5e3ace8f483842559e"
BASE_TREE="59c59fc99c8e553aa9982c6adf228b390ffb683d"
COMMIT_MSG="pyrate-limiter-casb-001 baseline: BoundedLimiter stub, state-management doc, visible tests"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MODE="offline"
if [ "${1:-}" = "--upstream" ]; then
  MODE="upstream"
  shift
fi
WORK="${1:-$(mktemp -d)}"
DEST="$WORK/pyrate_limiter"

if [ "$MODE" = "upstream" ]; then
  git clone --quiet --config core.autocrlf=false --config core.eol=lf \
      "$UPSTREAM_URL" "$DEST"
  cd "$DEST"
  git -c advice.detachedHead=false checkout --quiet "$UPSTREAM_COMMIT"
  got_upstream="$(git rev-parse 'HEAD^{tree}')"
  if [ "$got_upstream" != "$UPSTREAM_TREE" ]; then
    echo "MISMATCH: upstream tree is $got_upstream, expected $UPSTREAM_TREE" >&2
    exit 1
  fi
  git config core.autocrlf false
  git config core.eol lf
  git apply --binary "$HERE/upstream_delta.patch"
else
  mkdir -p "$DEST"
  cd "$DEST"
  git init -q
  git config core.autocrlf false
  git config core.eol lf
  git apply --binary "$HERE/baseline.patch"
fi

git add -A
GIT_AUTHOR_DATE="2026-08-11T00:00:00+00:00" \
GIT_COMMITTER_DATE="2026-08-11T00:00:00+00:00" \
git -c user.name="Task Author" -c user.email="author@example.com" \
    -c commit.gpgsign=false commit --quiet -m "$COMMIT_MSG"

RECON_TREE="$(git rev-parse 'HEAD^{tree}')"
RECON_COMMIT="$(git rev-parse HEAD)"
echo "mode:                    $MODE"
echo "recorded base tree:      $BASE_TREE"
echo "reconstructed base tree: $RECON_TREE"
echo "recorded base commit:    $BASE_COMMIT (offline mode only)"
echo "reconstructed commit:    $RECON_COMMIT"

status=0
if [ "$RECON_TREE" != "$BASE_TREE" ]; then
  echo "MISMATCH: reconstructed base tree differs from recorded base tree." >&2
  status=1
fi
# The commit hash is only expected to match in offline mode. In upstream mode
# the baseline commit has upstream history as its parent, so its hash differs by
# construction; the tree is what identifies the baseline.
if [ "$MODE" = "offline" ] && [ "$RECON_COMMIT" != "$BASE_COMMIT" ]; then
  echo "MISMATCH: reconstructed commit differs (identity/timestamps drifted)." >&2
  status=1
fi
if [ "$status" -eq 0 ]; then
  echo "OK: reconstruction matches tree and commit exactly."
fi
echo
echo "To confirm the shipped working tree matches the reconstruction:"
echo "  diff -rq --exclude=.git \"$HERE/../repo/src\" \"$DEST\""
exit "$status"
