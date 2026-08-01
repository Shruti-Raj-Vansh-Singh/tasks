# Provenance

This task's baseline is a small, self-contained `bg` workspace reconstructed from
a single scaffolding patch. It is **not** a checkout of an upstream repository:
the host library (`bagit`) is a pinned pip dependency, not part of the edited
tree.

- Host library: `bagit` (bagit-python) -- the Library of Congress reference BagIt
  implementation
- Host library repo: `https://github.com/LibraryOfCongress/bagit-python`
- Host library license: Public Domain (US Library of Congress work; PyPI
  classifier `License :: Public Domain`)
- Host library tag: `1.9.0`
- Pinned as: `bagit==1.9.0`
- Base commit: none -- the base is an empty-tree reconstruction (see below)
- Base tree: `b870c0046c31faa28111d6fcde92be13cdbea746`
- Scaffolding commit message:
  `bg bag-ingest helper scaffolding: ingest_bag stub, docs, visible tests`

## Empty-tree reconstruction model

Unlike a task built on a forked upstream checkout (where the base = upstream tag +
one scaffolding commit), the `bg` workspace has no upstream repo of its own. It is
purpose-built code that merely *imports* the `bagit` library. There is therefore
no meaningful "base commit" on top of an upstream tree; the base is defined
entirely by its **tree hash** (`b870c0046c31faa28111d6fcde92be13cdbea746`), which
is reproduced by applying `baseline.patch` to an EMPTY git tree.

## What the scaffolding patch adds

`baseline.patch` creates every file of the `bg` workspace from nothing (it applies
cleanly to an empty repository):

- `bg/ingest.py` - the unimplemented `ingest_bag(bag_dir)`; the function is
  declared and documented but raises `NotImplementedError`.
- `bg/__init__.py` - the package init (re-exports `ingest_bag`).
- `docs/ingesting.rst` - the bag-ingest walkthrough (describes the `Bag.info` /
  `Bag.entries` / `Bag.payload_files()` API the helper builds on and the record
  shape; names the manifests as the record of each payload file's hash).
- `INGEST_TASK.md` - the agent prompt.
- `bg_tests/__init__.py`, `bg_tests/_mkbag.py`, and `bg_tests/test_ingest.py` -
  the visible tests (ordinary, well-formed bags whose bytes match their
  manifests) plus a helper that builds a well-formed bag with `bagit.make_bag`.

The `bg` package is pure Python and imports directly from the checkout; its only
runtime dependency is the pinned `bagit` library, so no build step or generated
version file is needed.

The visible tests live in a top-level `bg_tests/` directory so the suite runs on
its own with only pytest and the pinned `bagit` library.

## Verify

```bash
bash reconstruct.sh /tmp/bg_recon
# inits an empty repo, applies baseline.patch, commits with the same message,
# and asserts the reconstructed HEAD^{tree} == b870c004...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  ../repo /tmp/bg_recon/bg
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim (INGEST_TASK.md is included in repo/, matching the reconstructed
# tree; nothing is excluded from the tree comparison).
```
