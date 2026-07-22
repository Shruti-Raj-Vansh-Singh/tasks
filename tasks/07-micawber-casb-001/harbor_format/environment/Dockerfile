FROM python:3.11-slim

ARG REPO_URL=https://github.com/coleifer/micawber.git
ARG UPSTREAM_COMMIT=46fa8e11ac7274ad6f729fea8b09d14eb63c5cf1
ARG BASE_COMMIT=31cde8b2df51f8cc10315b163ef45b8ac27761b6
# BASE_COMMIT is the task baseline: micawber 0.7.0
# (upstream 46fa8e11ac7274ad6f729fea8b09d14eb63c5cf1) plus one scaffolding
# commit that adds the unimplemented GuardedFetcher stub, the network access
# policy doc, and the visible tests. The image reconstructs it from provenance
# so no repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/micawber \
    PYTHONPATH=/workspace/micawber

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
         -m "Add GuardedFetcher stub, network access policy doc, and tests (feature unimplemented)"

WORKDIR /workspace/micawber

# micawber's only runtime dependency is beautifulsoup4. The GuardedFetcher
# feature and its oracles use only the standard library (urllib, ipaddress,
# socket) plus pytest for the visible tests; the oracles serve a fake HTTP
# transport and never touch the network. We run against the checkout via
# PYTHONPATH rather than installing the package.
RUN python -m pip install --upgrade pip \
    && python -m pip install "beautifulsoup4>=4.4" pytest

CMD ["python", "-m", "pytest", "micawber/tests_guarded.py", "-q", "-o", "addopts="]
