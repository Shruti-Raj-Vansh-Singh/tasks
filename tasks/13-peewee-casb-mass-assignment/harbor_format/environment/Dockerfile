FROM python:3.11-slim

ARG REPO_URL=https://github.com/coleifer/peewee.git
ARG UPSTREAM_COMMIT=65c793b559edc56ff7f44f8b6ca1c8c0bf574efa
ARG BASE_COMMIT=72c825836d37bfcdeb49122496e766d3ac78ae8e
# BASE_COMMIT is the task baseline: peewee 4.2.6
# (upstream 65c793b559edc56ff7f44f8b6ca1c8c0bf574efa) plus one scaffolding
# commit that adds the unimplemented ProfileUpdater stub, the model-update-safety
# doc, and the visible tests. The image reconstructs it from provenance so no
# repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/peewee \
    PYTHONPATH=/workspace/peewee

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
         -m "Add profile updater stub, model-update-safety doc, and tests (feature unimplemented)"

WORKDIR /workspace/peewee

# peewee is a pure-Python ORM with no runtime dependencies (sqlite via the
# standard library), so pytest is the only test tool needed. The feature and its
# oracles use an in-memory sqlite model; the visible tests live in
# tests/test_profile_service.py. We run against the checkout via PYTHONPATH.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "tests/test_profile_service.py", "-q"]
