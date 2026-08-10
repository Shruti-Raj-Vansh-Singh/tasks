# Baseline Repo Layout

This task is self-contained. Two things live here:

- `repo/src/` — the editable task workspace (the `cf` package). Run
  commands assume `repo/src/` is the working root. The task brief is
  `repo/src/CHANGEFEED_TASK.md`, the code to complete is `repo/src/changefeed/record.py`, and
  the visible tests are under `repo/src/changefeed_tests/`.
- `repo/vendor/dictdiffer/` — the complete source of the pinned upstream
  dependency `dictdiffer==0.10.0` (the exact sdist the build installs), vendored so
  the repository is fully browsable and independent of PyPI availability.

The build environment installs `dictdiffer==0.10.0` from the vendored source (or the
equivalent pinned PyPI release); the workspace imports it but does not modify
it.
