FROM python:3.12-slim

ARG REPO_URL=https://github.com/andialbrecht/sqlparse.git
ARG BASE_COMMIT=0d240230939bfb3b751b504878b1c7df04a3cab3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/sqlparse

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git checkout "$BASE_COMMIT"

WORKDIR /workspace/sqlparse

# Add the task scaffolding: the unimplemented redact_literals stub and its
# design note. The agent implements the stub; the feature is not upstream.
COPY scaffold/sqlparse/redaction.py /workspace/sqlparse/sqlparse/redaction.py
COPY scaffold/docs/redaction.md /workspace/sqlparse/docs/redaction.md

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e . pytest
