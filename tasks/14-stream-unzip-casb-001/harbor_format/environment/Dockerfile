FROM python:3.11-slim

ARG REPO_URL=https://github.com/uktrade/stream-unzip.git
ARG UPSTREAM_COMMIT=65cf30de8c389bd0cf39d3aa20e8843d7059618c
ARG BASE_COMMIT=afe518c595873d42e88ca2b6ed644a74e06e0954
# BASE_COMMIT is the task baseline: stream-unzip v0.0.95
# (upstream 65cf30de8c389bd0cf39d3aa20e8843d7059618c) plus one scaffolding
# commit that adds the unimplemented extract_to_dir stub, the extraction-safety
# doc, and the visible tests. The image reconstructs it from provenance so no
# repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/stream-unzip \
    PYTHONPATH=/workspace/stream-unzip

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
         -m "Add extract-to-dir stub, extraction-safety doc, and tests (feature unimplemented)"

WORKDIR /workspace/stream-unzip

# stream-unzip imports pycryptodome (AES-encrypted ZIPs) and stream-inflate
# (Deflate64) at module top, so both are required to import the package at all.
# The task and its oracles use only plain deflate/stored archives, but the
# imports must resolve, so we install both runtime deps plus pytest.
RUN python -m pip install --upgrade pip \
    && python -m pip install pycryptodome stream-inflate pytest trio

CMD ["python", "-m", "pytest", "test_extract.py", "-q", "-o", "addopts="]
