FROM python:3.12-slim

ARG REPO_URL=https://github.com/pallets/jinja.git
ARG UPSTREAM_COMMIT=15206881c006c79667fe5154fe80c01c65410679
ARG BASE_COMMIT=197bd3f6f75e002d192453a83ef9dd0970247486
# BASE_COMMIT is the task baseline: Jinja2 3.1.6
# (upstream 15206881c006c79667fe5154fe80c01c65410679) plus one scaffolding
# commit that adds the unimplemented notification-template renderer
# (src/notifier/render.py with the Alert dataclass + the notifier package
# marker), the agent prompt (NOTIFY_TASK.md), and the visible tests
# (notifier_tests/test_render.py). The image reconstructs it from provenance so
# no repo is shipped in this folder.
#
# jinja2 is pure Python; it is installed editable so it imports from the
# checkout and its one runtime dependency (markupsafe) is present. pytest is
# added for the visible suite.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/jinja

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
         -m "Add operator notification template rendering stub, ticket, and visible tests (feature unimplemented)"

WORKDIR /workspace/jinja

RUN python -m pip install --upgrade pip \
    && python -m pip install -e . \
    && python -m pip install pytest
