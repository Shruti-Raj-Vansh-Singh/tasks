FROM python:3.12-slim

ARG RPMFILE_VERSION=2.2.1
ARG BASE_TREE=c57553871b42512b9c7cb77c0b1163a14b288b58
# BASE_TREE is the task baseline: a small `rpmkit` workspace (the unimplemented
# install_rpm stub in rpmkit/install.py, the docs/unpacking.md walkthrough, the
# UNPACK_TASK.md prompt, and the visible tests in rpmkit_tests/test_install.py).
# The workspace is self-contained -- it has no upstream repo of its own; the
# `rpmfile` library it builds on is a pinned pip dependency. The image
# reconstructs the base tree deterministically by applying baseline.patch to an
# empty git tree (git verifies the resulting tree hash equals BASE_TREE).
#
# `rpmfile` 2.2.1 (srossross/rpmfile, tag v2.2.1 =
# c71e53491bb3ae8581e32630089c174b99b2aba6) is pure Python and installed from
# PyPI; only pytest is needed on top to run the visible suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/rpmkit

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
         -m "rpmkit RPM-unpack helper scaffolding: install_rpm stub, docs, visible tests" \
    && got="$(git rev-parse HEAD^{tree})" \
    && if [ "$got" != "$BASE_TREE" ]; then \
         echo "base tree mismatch: got $got want $BASE_TREE" >&2; exit 1; \
       fi

WORKDIR /workspace/rpmkit

RUN python -m pip install --upgrade pip \
    && python -m pip install "rpmfile==${RPMFILE_VERSION}" pytest
