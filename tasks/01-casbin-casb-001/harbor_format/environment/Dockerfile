FROM python:3.12-slim

ARG REPO_URL=https://github.com/casbin/pycasbin.git
ARG BASE_COMMIT=780c97f6bf13c00c46df685eb9954616ce4672b8
# BASE_COMMIT is the task baseline: pycasbin v2.8.0
# (upstream f858158e85eb9abdf308fd356d0246b89922b11b) plus one scaffolding
# commit that adds the unimplemented PolicyAdminEnforcer stub, the
# policy-administration doc, the shared test helper, and the visible utility
# tests. The image reconstructs it from provenance so no repo is shipped in
# this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/casbin

RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Clone upstream, then apply the scaffolding patch to reach BASE_COMMIT's tree.
COPY baseline.patch /tmp/baseline.patch
RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git -c advice.detachedHead=false checkout f858158e85eb9abdf308fd356d0246b89922b11b \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "Add PolicyAdminEnforcer stub, policy administration doc, and utility tests (feature unimplemented)"

WORKDIR /workspace/casbin

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install simpleeval wcmatch pytest
