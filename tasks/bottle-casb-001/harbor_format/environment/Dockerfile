FROM python:3.11-slim

ARG REPO_URL=https://github.com/bottlepy/bottle.git
ARG UPSTREAM_COMMIT=18faf70f21ba2a96e92d407b06cc017061215bde
ARG BASE_COMMIT=db49b6b0a2ab9b283c2c0f50f7e69117f72cb3dd
# BASE_COMMIT is the task baseline: Bottle 0.13.4
# (upstream 18faf70f21ba2a96e92d407b06cc017061215bde) plus one scaffolding
# commit that adds the unimplemented IdempotencyStore stub, the
# request-deduplication doc, and the visible tests. The image reconstructs it
# from provenance so no repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/bottle \
    PYTHONPATH=/workspace/bottle

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
         -m "Add idempotency store stub, dedup semantics doc, and tests (feature unimplemented)"

WORKDIR /workspace/bottle

# Bottle is a single-file, zero-dependency framework, so pytest is the only test
# tool needed on top of the standard library. The feature and its oracles are
# pure in-process Python (no server, no network), and the visible tests live in
# test/test_idempotency.py. We run against the checkout via PYTHONPATH.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "test/test_idempotency.py", "-q"]
