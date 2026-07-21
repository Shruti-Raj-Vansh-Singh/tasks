FROM python:3.11-slim

ARG REPO_URL=https://github.com/vutran1710/PyrateLimiter.git
ARG UPSTREAM_COMMIT=8cb467ea54c68368eaf34deef1a6cc38c41218a2
ARG BASE_COMMIT=23b4a6e303f4b22e7489cbc4085186f62a815c62
# BASE_COMMIT is the task baseline: PyrateLimiter v3.9.0
# (upstream 8cb467ea54c68368eaf34deef1a6cc38c41218a2) plus one scaffolding
# commit that adds the unimplemented BoundedLimiter stub, the state-management
# doc, and the visible tests. The image reconstructs it from provenance so no
# repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/pyrate_limiter \
    PYTHONPATH=/workspace/pyrate_limiter

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
         -m "Add bounded limiter stub, state-management doc, and tests (feature unimplemented)"

WORKDIR /workspace/pyrate_limiter

# pyrate-limiter's core (InMemoryBucket, Limiter, Rate) has no runtime
# dependencies; the redis/psycopg/filelock backends are optional and are not
# imported unless instantiated. The task and its oracles only use the in-memory
# path, so pytest is the only thing we need on top of the standard library. We
# run against the checkout via PYTHONPATH rather than installing the package, so
# no poetry/PEP517 build step is required.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "tests/test_bounded_limiter.py", "-q", "-o", "addopts="]
