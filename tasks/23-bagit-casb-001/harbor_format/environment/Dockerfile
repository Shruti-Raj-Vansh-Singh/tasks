FROM python:3.12-slim

ARG BAGIT_VERSION=1.9.0
ARG BASE_TREE=b870c0046c31faa28111d6fcde92be13cdbea746
# BASE_TREE is the task baseline: a small `bg` workspace (the unimplemented
# ingest_bag stub in bg/ingest.py, the docs/ingesting.rst walkthrough, the
# INGEST_TASK.md prompt, and the visible tests in bg_tests/test_ingest.py with
# the bg_tests/_mkbag.py helper). The workspace is self-contained -- it has no
# upstream repo of its own; the `bagit` library it builds on is a pinned pip
# dependency. The image reconstructs the base tree deterministically by applying
# baseline.patch to an empty git tree (git verifies the resulting tree hash
# equals BASE_TREE).
#
# `bagit` 1.9.0 (bagit-python, the Library of Congress reference BagIt
# implementation; Public Domain) is pure Python and installed from PyPI; only
# pytest is needed on top to run the visible suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/bg

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
         -m "bg bag-ingest helper scaffolding: ingest_bag stub, docs, visible tests" \
    && got="$(git rev-parse HEAD^{tree})" \
    && if [ "$got" != "$BASE_TREE" ]; then \
         echo "base tree mismatch: got $got want $BASE_TREE" >&2; exit 1; \
       fi

WORKDIR /workspace/bg

RUN python -m pip install --upgrade pip \
    && python -m pip install "bagit==${BAGIT_VERSION}" pytest
