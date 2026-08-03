# Baseline Repo Layout

This task is self-contained. Two things live here:

- `repo/src/` — the editable task workspace (the `bg` package). Run
  commands assume `repo/src/` is the working root. The task brief is
  `repo/src/INGEST_TASK.md`, the code to complete is `repo/src/bg/ingest.py`, and
  the visible tests are under `repo/src/bg_tests/`.
- `repo/vendor/bagit/` — the complete source of the pinned upstream
  dependency `bagit==1.9.0` (the exact sdist the build installs), vendored so
  the repository is fully browsable and independent of PyPI availability.

The build environment installs `bagit==1.9.0` from the vendored source (or the
equivalent pinned PyPI release); the workspace imports it but does not modify
it.
