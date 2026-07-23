# Provenance

This task's baseline is a small, self-contained `iw` workspace reconstructed from
a single scaffolding patch. It is **not** a checkout of an upstream repository:
the host library (`installer`) is a pinned pip dependency, not part of the edited
tree.

- Host library: `installer` -- pip's reference wheel installer
- Host library repo: `https://github.com/pypa/installer`
- Host library license: MIT
- Host library tag: `1.0.1`
- Host library commit: `dd0bc6af4888a884399e18b1393c4d9d6cbefa04` (peeled
  `7ffa96f4ada5f38792e340ba7f9e1c43e0104768`)
- Pinned as: `installer==1.0.1`
- Base commit: none -- the base is an empty-tree reconstruction (see below)
- Base tree: `06883390f77549e4f0581863834c5585480b6551`
- Scaffolding commit message:
  `iw wheel-install helper scaffolding: install_wheel stub, docs, visible tests`

## Empty-tree reconstruction model

Unlike a task built on a forked upstream checkout (where the base = upstream tag +
one scaffolding commit), the `iw` workspace has no upstream repo of its own. It is
purpose-built code that merely *imports* the `installer` library. There is
therefore no meaningful "base commit" on top of an upstream tree; the base is
defined entirely by its **tree hash**
(`06883390f77549e4f0581863834c5585480b6551`), which is reproduced by applying
`baseline.patch` to an EMPTY git tree.

## What the scaffolding patch adds

`baseline.patch` creates every file of the `iw` workspace from nothing (it applies
cleanly to an empty repository):

- `iw/apply.py` - the unimplemented `install_wheel(wheel_path, scheme_dirs)`; the
  function is declared and documented but raises `NotImplementedError`.
- `iw/__init__.py` - the package init.
- `docs/installing.rst` - the wheel-install walkthrough (describes the `WheelFile`
  / `SchemeDictionaryDestination` / `installer.install` API the helper builds on
  and the report shape; names `RECORD` as the manifest of contents).
- `INSTALL_TASK.md` - the agent prompt.
- `iw_tests/__init__.py` and `iw_tests/test_install.py` - the visible tests
  (ordinary, well-formed wheels whose bytes match their `RECORD`).

The `iw` package is pure Python and imports directly from the checkout; its only
runtime dependency is the pinned `installer` library, so no build step or
generated version file is needed.

The visible tests live in a top-level `iw_tests/` directory so the install suite
runs on its own with only pytest and the pinned `installer` library.

## Verify

```bash
bash reconstruct.sh /tmp/iw_recon
# inits an empty repo, applies baseline.patch, commits with the same message,
# and asserts the reconstructed HEAD^{tree} == 06883390...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  ../repo /tmp/iw_recon/iw
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim (INSTALL_TASK.md is included in repo/, matching the reconstructed
# tree; nothing is excluded from the tree comparison).
```
