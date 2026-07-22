FROM python:3.12-slim

ARG REPO_URL=https://github.com/urllib3/urllib3.git
ARG UPSTREAM_COMMIT=9a950b92d999f906b6020bb2d1076ee56cddd5d2
ARG BASE_COMMIT=0ed9356645d1c6321a30fcbb5e70050bd2bbb699
# BASE_COMMIT is the task baseline: urllib3 2.7.0
# (upstream 9a950b92d999f906b6020bb2d1076ee56cddd5d2) plus one scaffolding
# commit that adds the unimplemented WebhookDispatcher stub
# (src/urllib3/webhook.py), the outbound-delivery policy doc
# (docs/outbound-delivery.rst), and the visible tests
# (webhook_tests/test_webhook.py). The image reconstructs it from provenance so
# no repo is shipped in this folder.
#
# Python 3.12 is used deliberately: urllib3's own e2e/dummyserver suite has
# environmental failures on newer interpreters unrelated to this task, and 3.12
# keeps the webhook visible suite green with only pytest installed.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/urllib3

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
         -m "Add webhook dispatcher stub, outbound-delivery policy doc, and tests (feature unimplemented)"

WORKDIR /workspace/urllib3

# urllib3 uses hatch-vcs to generate src/urllib3/_version.py at build time; it is
# gitignored upstream and therefore not in the base tree. Write it explicitly so
# the checkout imports without a build step. urllib3 has zero unconditional
# runtime deps, so only pytest is needed to run the visible suite.
RUN printf '__version__ = "2.7.0"\n' > src/urllib3/_version.py \
    && python -m pip install --upgrade pip \
    && python -m pip install pytest
