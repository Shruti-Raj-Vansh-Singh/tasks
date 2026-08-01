# Provenance

This task's baseline is a small, self-contained `rpmkit` workspace reconstructed
from a single scaffolding patch. It is **not** a checkout of an upstream
repository: the host library (`rpmfile`) is a pinned pip dependency, not part of
the edited tree.

- Host library: `rpmfile` -- reads the RPM container format
- Host library repo: `https://github.com/srossross/rpmfile`
- Host library license: MIT (© Sean Ross-Ross)
- Host library tag: `v2.2.1`
- Host library commit: `c71e53491bb3ae8581e32630089c174b99b2aba6`
- Pinned as: `rpmfile==2.2.1`
- Base commit: none -- the base is an empty-tree reconstruction (see below)
- Base tree: `c57553871b42512b9c7cb77c0b1163a14b288b58`
- Scaffolding commit message:
  `rpmkit RPM-unpack helper scaffolding: install_rpm stub, docs, visible tests`

## Empty-tree reconstruction model

Unlike a task built on a forked upstream checkout (where the base = upstream tag +
one scaffolding commit), the `rpmkit` workspace has no upstream repo of its own.
It is purpose-built code that merely *imports* the `rpmfile` library. There is
therefore no meaningful "base commit" on top of an upstream tree; the base is
defined entirely by its **tree hash**
(`c57553871b42512b9c7cb77c0b1163a14b288b58`), which is reproduced by applying
`baseline.patch` to an EMPTY git tree.

## What the scaffolding patch adds

`baseline.patch` creates every file of the `rpmkit` workspace from nothing (it
applies cleanly to an empty repository):

- `rpmkit/install.py` - the unimplemented `install_rpm(rpm_path, dest_dir)`; the
  function is declared and documented but raises `NotImplementedError`.
- `rpmkit/__init__.py` - the package init.
- `docs/unpacking.md` - the RPM-unpack walkthrough (describes the `rpmfile` API
  the helper builds on -- `rpmfile.open`, `headers`, `getmembers`,
  `extractfile` -- the header file tables, and the report shape; names the
  `filemd5s`/`filesizes`/`basenames` tables as the per-file manifest).
- `UNPACK_TASK.md` - the agent prompt.
- `rpmkit_tests/__init__.py` and `rpmkit_tests/test_install.py` - the visible
  tests (ordinary, well-formed packages whose payload bytes match their header
  manifest).

The `rpmkit` package is pure Python and imports directly from the checkout; its
only runtime dependency is the pinned `rpmfile` library, so no build step or
generated version file is needed.

The visible tests live in a top-level `rpmkit_tests/` directory so the unpack
suite runs on its own with only pytest and the pinned `rpmfile` library.

## Verify

```bash
bash reconstruct.sh /tmp/rpmkit_recon
# inits an empty repo, applies baseline.patch, commits with the same message,
# and asserts the reconstructed HEAD^{tree} == c57553871b...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  ../repo /tmp/rpmkit_recon/rpmkit
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim (UNPACK_TASK.md is included in repo/, matching the reconstructed
# tree; nothing is excluded from the tree comparison).
```
