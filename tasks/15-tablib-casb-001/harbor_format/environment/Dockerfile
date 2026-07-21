FROM python:3.11-slim

ARG REPO_URL=https://github.com/jazzband/tablib.git
ARG UPSTREAM_COMMIT=bd2ea7ab80cb2f4e6326e5a823c46899186a188e
ARG BASE_COMMIT=18b652f8799bfd444cfb1a0c8b66d1c1daa220fb
# BASE_COMMIT is the task baseline: tablib v3.9.0
# (upstream bd2ea7ab80cb2f4e6326e5a823c46899186a188e) plus one scaffolding
# commit that adds the unimplemented export_sheet_csv stub, the cell-values
# doc, and the visible tests. The image reconstructs it from provenance so no
# repo is shipped in this folder.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/tablib \
    PYTHONPATH=/workspace/tablib/src

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
         -m "Add spreadsheet CSV export stub, cell-values doc, and tests (feature unimplemented)"

WORKDIR /workspace/tablib

# tablib has no required runtime dependencies; it is imported straight off the
# checkout via PYTHONPATH rather than installed. The utility/alignment oracles
# and the task's visible tests (tests/test_sheets.py) import only tablib and the
# standard library, so pytest is the only thing needed on top. The optional
# format extras (xlsx/ods/yaml/pandas/cli) and the repo's broader test suite are
# out of scope for this task's verifier.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "tests/test_sheets.py", "-q", "-o", "addopts="]
