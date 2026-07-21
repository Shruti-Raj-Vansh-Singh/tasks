FROM python:3.12-slim

ARG REPO_URL=https://github.com/hynek/structlog.git
ARG BASE_COMMIT=f94242a13b146554810655819a861bbfc8a851ba
# BASE_COMMIT is the task baseline: structlog 26.1.0
# (upstream 8174a86a2f14b5bd295eded733ff5fffc12aa173) plus one scaffolding
# commit that adds the unimplemented AuditLineRenderer stub, the audit-log
# format doc, and the visible tests. The image reconstructs it from provenance
# so no repo is shipped in this folder.
#
# Python 3.12 is used deliberately: structlog 26.1.0's CallsiteParameterAdder
# e2e tests fail on 3.14 for reasons unrelated to this task, so pinning 3.12
# keeps the upstream suite green.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/structlog

RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Clone upstream, then apply the scaffolding patch to reach BASE_COMMIT's tree.
COPY baseline.patch /tmp/baseline.patch
RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git -c advice.detachedHead=false checkout 8174a86a2f14b5bd295eded733ff5fffc12aa173 \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "Add single-line audit renderer stub, format doc, and tests (feature unimplemented)"

WORKDIR /workspace/structlog

# Runtime dep (typing-extensions), pytest, and the dev test deps structlog's
# own suite imports (time-machine / freezegun / pretend) so run_visible_tests.sh
# can exercise the upstream renderer tests.
RUN python -m pip install --upgrade pip \
    && python -m pip install typing-extensions pytest time-machine freezegun pretend
