FROM python:3.12-slim

ARG INSTALLER_VERSION=1.0.1
ARG BASE_TREE=06883390f77549e4f0581863834c5585480b6551
# BASE_TREE is the task baseline: a small `iw` workspace (the unimplemented
# install_wheel stub in iw/apply.py, the docs/installing.rst walkthrough, the
# INSTALL_TASK.md prompt, and the visible tests in iw_tests/test_install.py).
# The workspace is self-contained -- it has no upstream repo of its own; the
# `installer` library it builds on is a pinned pip dependency. The image
# reconstructs the base tree deterministically by applying baseline.patch to an
# empty git tree (git verifies the resulting tree hash equals BASE_TREE).
#
# `installer` 1.0.1 (pypa/installer, tag 1.0.1 =
# dd0bc6af4888a884399e18b1393c4d9d6cbefa04) is pure Python and installed from
# PyPI; only pytest is needed on top to run the visible suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/iw

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
         -m "iw wheel-install helper scaffolding: install_wheel stub, docs, visible tests" \
    && got="$(git rev-parse HEAD^{tree})" \
    && if [ "$got" != "$BASE_TREE" ]; then \
         echo "base tree mismatch: got $got want $BASE_TREE" >&2; exit 1; \
       fi

WORKDIR /workspace/iw

RUN python -m pip install --upgrade pip \
    && python -m pip install "installer==${INSTALLER_VERSION}" pytest
