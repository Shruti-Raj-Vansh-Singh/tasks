FROM python:3.11-slim

ARG REPO_URL=https://github.com/celery/kombu.git
ARG UPSTREAM_COMMIT=279b81f3042f23524111d3afcc773e8bb5530672
ARG BASE_COMMIT=bfc77077d0075b068761e91e052dc00513df43c0
# BASE_COMMIT is the task baseline: kombu v5.6.2
# (upstream 279b81f3042f23524111d3afcc773e8bb5530672) plus one scaffolding
# commit that adds the unimplemented decompress_bounded stub, the untrusted-
# message policy doc, and the visible tests. The image reconstructs it from
# provenance so no repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/kombu \
    PYTHONPATH=/workspace/kombu

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
         -m "Add bounded-decompression stub, untrusted-message doc, and tests (feature unimplemented)"

WORKDIR /workspace/kombu

# Install kombu and its runtime dependencies (amqp, vine, tzdata, packaging) so
# kombu.compression / kombu.safe_compression import cleanly, plus pytest for the
# visible tests. The feature and its oracles use only the standard library
# (zlib, bz2, lzma, tracemalloc); the oracles build in-memory compressed
# payloads and never contact a broker.
RUN python -m pip install --upgrade pip \
    && python -m pip install -e . pytest

CMD ["python", "-m", "pytest", "t/unit/test_safe_compression.py", "-q", "-o", "addopts="]
