# Provenance

This task's baseline is pycasbin `v2.8.0` plus one scaffolding commit.

- Upstream repo: `https://github.com/casbin/pycasbin`
- Upstream license: Apache-2.0
- Upstream tag: `v2.8.0`
- Upstream commit: `f858158e85eb9abdf308fd356d0246b89922b11b`
- Base commit: `6279b3d91c3d1c9a2cdbc9539e1b0bb8143cd18b`
- Base tree: `21da682d7b32558b51b646891c9c9b0910d557f8`
- Scaffolding commit message:
  `Add cached enforcer stub, policy consistency doc, and tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds only:

- `casbin/cached_enforcer.py` - the unimplemented `CachedEnforcer` stub
  (`raise NotImplementedError`).
- `casbin/__init__.py` - one line exporting `CachedEnforcer`.
- `docs/policy_consistency.md` - the discoverable read-after-write rule page.
- `tests/test_cached_enforcer.py` - the visible tests.
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

No existing casbin source is modified.

## Verify

```bash
bash reconstruct.sh /tmp/casb_recon
# clones upstream at the tag, applies baseline.patch, commits with the same
# message, and asserts the reconstructed HEAD^{tree} == 21da682d...

diff -rq --exclude=.git ../repo/src /tmp/casb_recon/casbin
# expected: no differences (the shipped repo/src is byte-identical to the
# reconstructed base tree; both are LF on disk).
```

The shipped `repo/src/` working tree is normalized to LF on disk so the tree
hash and the `diff -rq` both match exactly.
