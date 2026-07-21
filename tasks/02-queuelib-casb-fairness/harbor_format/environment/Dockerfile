FROM python:3.12-slim

ARG REPO_URL=https://github.com/scrapy/queuelib.git
ARG BASE_COMMIT=06f63bb6e870fd45ea608e076ea84896c5f92821

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/queuelib

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone "$REPO_URL" "$REPO_UNDER_TEST" \
    && cd "$REPO_UNDER_TEST" \
    && git checkout "$BASE_COMMIT"

WORKDIR /workspace/queuelib

# Add the task scaffolding on top of the pinned upstream checkout: the
# unimplemented FairPriorityQueue stub and its design note. The agent
# implements the stub; the feature is NOT present upstream.
COPY scaffold/queuelib/fairqueue.py /workspace/queuelib/queuelib/fairqueue.py
COPY scaffold/docs/fair_priority_queue.md /workspace/queuelib/docs/fair_priority_queue.md

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install -e . pytest
