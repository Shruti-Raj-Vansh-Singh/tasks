FROM python:3.12-slim

ARG DICTDIFFER_VERSION=0.10.0
ARG BASE_TREE=dddc64b2e7ee164a6a6c4d409b2cd148acb10476
# BASE_TREE is the task baseline: a small `cf` workspace (the unimplemented
# record_change stub in changefeed/record.py, the ChangeFeed store in
# changefeed/feed.py, the docs/recording.rst walkthrough, the CHANGEFEED_TASK.md
# prompt, and the visible tests in changefeed_tests/test_record.py). The
# workspace is self-contained -- it has no upstream repo of its own; the
# `dictdiffer` library it builds on is a pinned pip dependency. The image
# reconstructs the base tree deterministically by applying baseline.patch to an
# empty git tree (git verifies the resulting tree hash equals BASE_TREE).
#
# `dictdiffer` 0.10.0 (inveniosoftware/dictdiffer; MIT) is pure Python and
# installed from PyPI; only pytest is needed on top to run the visible suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/cf

RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Reconstruct the base tree: init an empty repo, apply the scaffolding patch
# (which creates every workspace file), commit, and assert the tree hash.
COPY baseline.patch /tmp/baseline.patch
RUN mkdir -p "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git init -q \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "changefeed activity-feed recorder scaffolding: record_change stub, docs, visible tests" \
    && got="$(git rev-parse HEAD^{tree})" \
    && if [ "$got" != "$BASE_TREE" ]; then \
         echo "base tree mismatch: got $got want $BASE_TREE" >&2; exit 1; \
       fi

WORKDIR /workspace/cf

RUN python -m pip install --upgrade pip \
    && python -m pip install "dictdiffer==${DICTDIFFER_VERSION}" pytest
