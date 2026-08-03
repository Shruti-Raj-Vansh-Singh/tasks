# Baseline Repo Layout

This task is self-contained. Two things live here:

- `repo/src/` — the editable task workspace (the `rpmkit` package). Run
  commands assume `repo/src/` is the working root. The task brief is
  `repo/src/UNPACK_TASK.md`, the code to complete is `repo/src/rpmkit/install.py`, and
  the visible tests are under `repo/src/rpmkit_tests/`.
- `repo/vendor/rpmfile/` — the complete source of the pinned upstream
  dependency `rpmfile==2.2.1` (the exact sdist the build installs), vendored so
  the repository is fully browsable and independent of PyPI availability.

The build environment installs `rpmfile==2.2.1` from the vendored source (or the
equivalent pinned PyPI release); the workspace imports it but does not modify
it.
