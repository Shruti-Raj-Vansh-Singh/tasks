FROM python:3.11-slim

ARG REPO_URL=https://github.com/pyauth/pyotp.git
ARG UPSTREAM_COMMIT=81ed54ac7347fbac522ce9c6bd1bca8e18ad4603
ARG BASE_COMMIT=21a8d0cd05c25f97b0cab701e9b83f3f433c09f1
# BASE_COMMIT is the task baseline: pyotp v2.10.0
# (upstream 81ed54ac7347fbac522ce9c6bd1bca8e18ad4603) plus one scaffolding
# commit that adds the unimplemented ReplayGuard stub, the verification-state
# doc, and the visible tests. The image reconstructs it from provenance so no
# repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/pyotp \
    PYTHONPATH=/workspace/pyotp/src:/workspace/pyotp

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
         -m "Add replay guard stub, verification-state doc, and tests (feature unimplemented)"

WORKDIR /workspace/pyotp

# pyotp has no runtime dependencies (pure standard library), and the task and
# its oracles only import pyotp itself. We run against the checkout via
# PYTHONPATH rather than installing the package (pyotp uses hatch-vcs, which
# needs git tags at build), so pytest is the only thing we install on top of
# the standard library.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "tests/test_replay_guard.py", "-q", "-o", "addopts="]
