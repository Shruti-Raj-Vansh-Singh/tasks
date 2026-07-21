FROM python:3.12-slim

ARG REPO_URL=https://github.com/peter-wangxu/persist-queue.git
ARG BASE_COMMIT=b4fb6d186e375850b2d9ac49fc635779be95f173

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/persist-queue

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git checkout "$BASE_COMMIT"

WORKDIR /workspace/persist-queue

# Add the task scaffolding: the unimplemented RedeliveryAckQueue stub and its
# design note. The agent implements the stub; the feature is not upstream.
COPY scaffold/persistqueue/redelivery.py /workspace/persist-queue/persistqueue/redelivery.py
COPY scaffold/docs/redelivery.md /workspace/persist-queue/docs/redelivery.md

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e . pytest
