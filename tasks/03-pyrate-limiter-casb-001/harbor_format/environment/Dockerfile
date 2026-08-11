FROM python:3.11-slim

ARG BASE_TREE=59c59fc99c8e553aa9982c6adf228b390ffb683d
# BASE_TREE is the task baseline: PyrateLimiter v3.9.0 (upstream
# 8cb467ea54c68368eaf34deef1a6cc38c41218a2, MIT) plus one scaffolding commit
# that adds the unimplemented BoundedLimiter stubs, docs/limiter_state_management.md,
# and tests/test_bounded_limiter.py. `baseline.patch` in this folder is a full
# binary-safe creation patch for that whole tree, so the image is built with no
# network access at all -- nothing is cloned and nothing but pinned pip wheels is
# fetched. git verifies the reconstructed tree hash equals BASE_TREE, so a
# corrupted or edited patch fails the build instead of silently shifting the
# baseline. The same tree is vendored in the package at
# ../../turing_format/repo/src.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    REPO_UNDER_TEST=/workspace/pyrate_limiter \
    PYTHONPATH=/workspace/pyrate_limiter

# git is here so the agent can diff and commit its own work and so solve.sh can
# apply a patch; it is never used to fetch anything.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Reconstruct the base tree offline: init an empty repo, apply the creation
# patch, commit with fixed identity and timestamps, assert the tree hash.
COPY baseline.patch /tmp/baseline.patch
RUN mkdir -p "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git init -q \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply --binary /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && GIT_AUTHOR_DATE="2026-08-11T00:00:00+00:00" \
       GIT_COMMITTER_DATE="2026-08-11T00:00:00+00:00" \
       git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "pyrate-limiter-casb-001 baseline: BoundedLimiter stub, state-management doc, visible tests" \
    && got="$(git rev-parse HEAD^{tree})" \
    && if [ "$got" != "$BASE_TREE" ]; then \
         echo "base tree mismatch: got $got want $BASE_TREE" >&2; exit 1; \
       fi

WORKDIR /workspace/pyrate_limiter

# pyrate-limiter's core (InMemoryBucket, Limiter, Rate) has no runtime
# dependencies; the redis/psycopg/filelock backends are optional and are not
# imported unless instantiated. The task and its oracles only use the in-memory
# path, so pytest is the only thing needed on top of the standard library. We run
# against the checkout via PYTHONPATH rather than installing the package, so no
# poetry/PEP517 build step is required. Both are pinned so a future release
# cannot change what a graded rollout sees.
RUN python -m pip install "pip==24.2" \
    && python -m pip install "pytest==8.3.3"

CMD ["python", "-m", "pytest", "tests/test_bounded_limiter.py", "-q", "-o", "addopts="]
