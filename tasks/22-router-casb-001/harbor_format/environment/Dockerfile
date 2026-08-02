FROM python:3.12-slim

ARG REPO_URL=https://github.com/zopefoundation/RestrictedPython.git
ARG UPSTREAM_COMMIT=aff96dd7e425de1288eb3737f3b20d2a8de4bb28
# BASE_COMMIT is the task baseline: RestrictedPython 8.4
# (upstream aff96dd7e425de1288eb3737f3b20d2a8de4bb28) plus one scaffolding
# commit that adds the unimplemented routing-rule helper
# (router/rules.py with the Alert record + Team and the evaluate_rule stub,
# router/__init__.py), the agent prompt (TASK.md), and the visible tests
# (router_tests/test_rules.py + router_tests/__init__.py). The image
# reconstructs it from provenance so no repo is shipped in this folder. The
# recorded base tree is 99291a7b035688c1b1a81715f78bb61116d98605 and, with the
# fixed author/committer identity + dates below, the base commit is
# 70da1e6b16b4307f038a4670aa2b2bc306bc08b0 (reproducible).
#
# The RestrictedPython checkout uses a src/ layout (src/RestrictedPython/); the
# agent edits /workspace/app/router/rules.py. RestrictedPython is also
# pip-installed at the pinned version so `import RestrictedPython` resolves
# whether or not src/ is on the path.

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
       GIT_AUTHOR_DATE="2026-08-01T00:00:00 +0000" \
       GIT_COMMITTER_DATE="2026-08-01T00:00:00 +0000" \
       git -c commit.gpgsign=false commit -q \
         -m "Add routing-rule stub, ticket, and visible tests (feature unimplemented)"

WORKDIR /workspace/app

RUN python -m pip install --upgrade pip \
    && python -m pip install RestrictedPython==8.4 pytest
