FROM python:3.12-slim

ARG REPO_URL=https://github.com/pallets/jinja.git
ARG UPSTREAM_COMMIT=15206881c006c79667fe5154fe80c01c65410679
# BASE_COMMIT is the task baseline: jinja 3.1.6
# (upstream 15206881c006c79667fe5154fe80c01c65410679) plus one scaffolding
# commit that adds the unimplemented notification-render helper
# (notifier/render.py with the Alert record + render_notification stub,
# notifier/__init__.py), the agent prompt (TASK.md), and the visible tests
# (notifier_tests/test_render.py + notifier_tests/__init__.py). The image
# reconstructs it from provenance so no repo is shipped in this folder. The
# recorded base tree is 9ede8495227343a2a3837193a0c7adb87b52e6a6 and, with the
# fixed author/committer identity + dates below, the base commit is
# ca6365b8d667e9f152e76355d6f6ac805e252d39 (reproducible).
#
# The jinja checkout under test uses a src/ layout (src/jinja2/); the agent
# edits /workspace/app/notifier/render.py. jinja2 is also pip-installed at the
# pinned version so `import jinja2` resolves whether or not src/ is on the path.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Clone upstream, then apply the scaffolding patch to reach the base tree.
COPY baseline.patch /tmp/baseline.patch
RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git -c advice.detachedHead=false checkout "$UPSTREAM_COMMIT" \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git apply /tmp/baseline.patch \
    && git add -A \
    && GIT_AUTHOR_NAME="Task Author" GIT_AUTHOR_EMAIL="author@example.com" \
       GIT_COMMITTER_NAME="Task Author" GIT_COMMITTER_EMAIL="author@example.com" \
       GIT_AUTHOR_DATE="2026-07-23T00:00:00 +0000" \
       GIT_COMMITTER_DATE="2026-07-23T00:00:00 +0000" \
       git -c commit.gpgsign=false commit -q \
         -m "Add notification-render stub, ticket, and visible tests (feature unimplemented)"

WORKDIR /workspace/app

RUN python -m pip install --upgrade pip \
    && python -m pip install jinja2==3.1.6 pytest
