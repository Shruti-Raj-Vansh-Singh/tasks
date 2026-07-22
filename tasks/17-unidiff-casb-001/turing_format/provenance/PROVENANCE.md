# Provenance

This task's baseline is unidiff `v0.7.5` plus one scaffolding commit.

- Upstream repo: `https://github.com/matiasb/python-unidiff`
- Upstream license: MIT
- Upstream tag: `v0.7.5`
- Upstream commit: `ab8fcd4fce0c5e75dd016e4f1df19faed1333810`
- Base commit: `643214ed04254e1256e6692a0316db5d3994fe2d`
- Base tree: `0f3c68227c42fd8c53b8c65d701e8712c0b7e12f`
- Scaffolding commit message:
  `Add patch-apply helper stub, working-copy doc, and tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds four
new files and appends one export line to `unidiff/__init__.py`, modifying no
other upstream source:

- `unidiff/apply.py` - the unimplemented `apply_patchset_to_dir(patch_text,
  dest_root)`; the function is declared and documented but raises
  `NotImplementedError`.
- `unidiff/__init__.py` - one added line exporting `apply_patchset_to_dir` from
  the package.
- `docs/working_copy.rst` - the working-copy apply doc (describes the
  `PatchSet` / `PatchedFile` / `Hunk` API the helper builds on and the report
  shape).
- `APPLY_TASK.md` - the agent prompt.
- `patch_tests/test_apply.py` - the visible tests (ordinary, well-formed
  patches over matching working copies).

unidiff is pure Python with zero runtime dependencies and imports directly from
the checkout, so no build step or generated version file is needed.

The visible tests live in a top-level `patch_tests/` directory rather than under
unidiff's own `tests/` so the apply suite runs on its own with only pytest,
independent of the library's parser test fixtures.

## Verify

```bash
bash reconstruct.sh /tmp/ud_recon
# clones upstream at the tag, applies baseline.patch, commits with the same
# message, and asserts the reconstructed HEAD^{tree} == 0f3c6822...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  --exclude=APPLY_TASK.md ../repo /tmp/ud_recon/unidiff
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim; APPLY_TASK.md is excluded only because the shipped repo/ presents
# the prompt separately at the package root rather than inside the checkout.
```
