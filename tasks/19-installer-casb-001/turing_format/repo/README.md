# Baseline Repo Layout

This task is self-contained. Two things live here:

- `repo/src/` — the editable task workspace (the `iw` package). Run
  commands assume `repo/src/` is the working root. The task brief is
  `repo/src/INSTALL_TASK.md`, the code to complete is `repo/src/iw/apply.py`, and
  the visible tests are under `repo/src/iw_tests/`.
- `repo/vendor/installer/` — the complete source of the pinned upstream
  dependency `installer==1.0.1` (the exact sdist the build installs), vendored so
  the repository is fully browsable and independent of PyPI availability.

The build environment installs `installer==1.0.1` from the vendored source (or the
equivalent pinned PyPI release); the workspace imports it but does not modify
it.
