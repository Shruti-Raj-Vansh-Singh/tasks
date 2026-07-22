FROM python:3.12-slim

ARG REPO_URL=https://github.com/matiasb/python-unidiff.git
ARG UPSTREAM_COMMIT=ab8fcd4fce0c5e75dd016e4f1df19faed1333810
ARG BASE_COMMIT=643214ed04254e1256e6692a0316db5d3994fe2d
# BASE_COMMIT is the task baseline: unidiff v0.7.5
# (upstream ab8fcd4fce0c5e75dd016e4f1df19faed1333810) plus one scaffolding
# commit that adds the unimplemented patch-apply helper
# (unidiff/apply.py, exported from unidiff/__init__.py), the working-copy doc
# (docs/working_copy.rst), the agent prompt (APPLY_TASK.md), and the visible
# tests (patch_tests/test_apply.py). The image reconstructs it from provenance
# so no repo is shipped in this folder.
#
# unidiff is pure Python with zero runtime dependencies and imports directly
# from the checkout (no build step); only pytest is needed to run the visible
# suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/unidiff

RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Clone upstream, then apply the scaffolding patch to reach BASE_COMMIT's tree.
COPY baseline.patch /tmp/baseline.patch
RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git -c advice.detachedHead=false checkout "$UPSTREAM_COMMIT" \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "Add patch-apply helper stub, working-copy doc, and tests (feature unimplemented)"

WORKDIR /workspace/unidiff

RUN python -m pip install --upgrade pip \
    && python -m pip install pytest
