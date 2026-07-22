FROM python:3.12-slim

ARG REPO_URL=https://github.com/tr11/python-configuration.git
ARG UPSTREAM_COMMIT=75137c6f476c52f4232abd447962665a12ab7aee
ARG BASE_COMMIT=b1716134bd38e9de4b67d150c3766a0ab7b0bb61
# BASE_COMMIT is the task baseline: python-configuration 0.12.1
# (upstream 75137c6f476c52f4232abd447962665a12ab7aee, tag 0.12.1) plus one
# scaffolding commit that adds the unimplemented build_effective_report stub, the
# layered-configuration doc, and the visible utility tests. The image
# reconstructs it from provenance so no repo is shipped in this folder. The
# importable package is upstream's src/config; the checkout root is
# /workspace/pyconf and src/ is placed on PYTHONPATH.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    REPO_UNDER_TEST=/workspace/pyconf \
    PYTHONPATH=/workspace/pyconf/src:/workspace/pyconf

RUN apt-get update && apt-get install -y --no-install-recommends \
    git patch \
    && rm -rf /var/lib/apt/lists/*

# Reconstruct the baseline: clone upstream at the pinned tag, lay out the
# pristine `config` package as src/config (dropping upstream's config/.gitignore
# and adding the setuptools-scm _version.py the package ships), then apply the
# scaffolding patch to reach the base tree (feature unimplemented).
COPY baseline.patch /tmp/baseline.patch
COPY _version.py /tmp/_version.py
RUN git clone "$REPO_URL" /tmp/upstream \
    && cd /tmp/upstream \
    && git -c advice.detachedHead=false checkout "$UPSTREAM_COMMIT" \
    && mkdir -p "$REPO_UNDER_TEST/src" \
    && cp -r /tmp/upstream/src/config "$REPO_UNDER_TEST/src/config" \
    && rm -f "$REPO_UNDER_TEST/src/config/.gitignore" \
    && cp /tmp/_version.py "$REPO_UNDER_TEST/src/config/_version.py" \
    && cd "$REPO_UNDER_TEST/src" \
    && git init -q \
    && git config core.autocrlf false \
    && git config core.eol lf \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q -m "python-configuration 0.12.1 (pristine)" \
    && git apply /tmp/baseline.patch \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false add -A \
    && git -c user.name="Task Author" -c user.email="author@example.com" \
         -c commit.gpgsign=false commit -q \
         -m "Add build_effective_report stub, layered-configuration doc, and visible utility tests (feature unimplemented)" \
    && rm -rf /tmp/upstream

WORKDIR /workspace/pyconf/src

# python-configuration's core needs no third-party runtime deps for this feature;
# build_effective_report and its oracles use only the standard library plus the
# vendored `config` package. pytest runs the visible/hidden tests. Everything is
# offline: the oracles build ConfigurationSet objects in-process from plain dicts
# and never touch the network. The only network use is this build's git clone.
RUN python -m pip install --upgrade pip \
    && python -m pip install pytest

CMD ["python", "-m", "pytest", "tests/utility", "-q", "-o", "addopts="]
