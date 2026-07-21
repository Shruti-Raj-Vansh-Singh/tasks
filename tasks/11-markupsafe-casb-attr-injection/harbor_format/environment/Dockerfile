FROM python:3.12-slim

ARG REPO_URL=https://github.com/pallets/markupsafe.git
ARG BASE_COMMIT=b2e4d9c7687be25695fffbe93a37622302b24fb1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/markupsafe

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git checkout "$BASE_COMMIT"

WORKDIR /workspace/markupsafe

# Add the task scaffolding: the unimplemented render_attributes stub and its
# design note. The agent implements the stub; the feature is not upstream.
COPY scaffold/markupsafe/attributes.py /workspace/markupsafe/src/markupsafe/attributes.py
COPY scaffold/docs/attributes.md /workspace/markupsafe/docs/attributes.md

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e . pytest
