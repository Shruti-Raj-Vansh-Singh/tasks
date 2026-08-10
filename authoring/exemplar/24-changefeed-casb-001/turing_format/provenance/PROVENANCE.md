# Provenance

This task's baseline is a small, self-contained `changefeed` workspace
reconstructed from a single scaffolding patch. It is **not** a checkout of an
upstream repository: the host library (`dictdiffer`) is a pinned pip dependency,
not part of the edited tree.

- Host library: `dictdiffer` (inveniosoftware/dictdiffer)
- Host library repo: `https://github.com/inveniosoftware/dictdiffer`
- Host library license: MIT (PyPI classifier `License :: OSI Approved :: MIT
  License`)
- Host library tag: `0.10.0`
- Pinned as: `dictdiffer==0.10.0`
- Base commit: none -- the base is an empty-tree reconstruction (see below)
- Base tree: `dddc64b2e7ee164a6a6c4d409b2cd148acb10476`
- Scaffolding commit message:
  `changefeed activity-feed recorder scaffolding: record_change stub, docs, visible tests`

## Empty-tree reconstruction model

Unlike a task built on a forked upstream checkout (where the base = upstream tag +
one scaffolding commit), the `changefeed` workspace has no upstream repo of its
own. It is purpose-built code that merely *imports* the `dictdiffer` library. There
is therefore no meaningful "base commit" on top of an upstream tree; the base is
defined entirely by its **tree hash**
(`dddc64b2e7ee164a6a6c4d409b2cd148acb10476`), which is reproduced by applying
`baseline.patch` to an EMPTY git tree.

## What the scaffolding patch adds

`baseline.patch` creates every file of the `changefeed` workspace from nothing (it
applies cleanly to an empty repository):

- `changefeed/record.py` - the unimplemented `record_change(feed, old_record,
  new_record)`; the function is declared and documented but raises
  `NotImplementedError`.
- `changefeed/__init__.py` - the package init.
- `changefeed/feed.py` - the `ChangeFeed` store (`append`, `entries`, `__len__`).
- `docs/recording.rst` - the change-recording walkthrough (describes the
  `dictdiffer.diff` API the helper builds on and the entry shape -- account, owner
  label, changes).
- `CHANGEFEED_TASK.md` - the agent prompt.
- `changefeed_tests/__init__.py` and `changefeed_tests/test_record.py` - the
  visible tests (ordinary plan/status edits and a no-op).

The `changefeed` package is pure Python and imports directly from the checkout;
its only runtime dependency is the pinned `dictdiffer` library, so no build step or
generated version file is needed.

The visible tests live in a top-level `changefeed_tests/` directory so the suite
runs on its own with only pytest and the pinned `dictdiffer` library.

## Verify

```bash
bash reconstruct.sh /tmp/cf_recon
# inits an empty repo, applies baseline.patch, commits with the same message,
# and asserts the reconstructed HEAD^{tree} == dddc64b2...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  ../repo /tmp/cf_recon/cf
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim (CHANGEFEED_TASK.md is included in repo/, matching the reconstructed
# tree; nothing is excluded from the tree comparison).
```
