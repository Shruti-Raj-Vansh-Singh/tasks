# Wire up "apply a patch to a working copy"

We keep hand-rolling the same "take a unified diff and edit a tree of files to
match it" logic in different tools -- the review-bot that lands a proposed
change, the migration runner that ships changes as diffs -- and each copy drifts.
I've started a single home for it next to the parser, in
`unidiff/apply.py`. The function is declared and documented there and exported
from `unidiff`; `apply_patchset_to_dir` just raises `NotImplementedError`.
Please fill it in.

## What it's for

A tool parses a unified diff with `unidiff.PatchSet` and wants to apply it to a
directory of files. Instead of each tool re-implementing the file I/O and the
per-hunk splicing, it calls one function:

```python
from unidiff import apply_patchset_to_dir

report = apply_patchset_to_dir(patch_text, dest_root)
```

`patch_text` is the unified diff (as produced by `git diff` / `diff -u`), which
may touch several files -- editing some, introducing new ones, removing others.
`dest_root` is the working copy the patch is applied within. The call edits the
files on disk and returns a `report` mapping each patched path to a short status
string.

## What `apply_patchset_to_dir` should do

- Parse `patch_text` into a `PatchSet` and walk its `PatchedFile`s.
- For each file, apply the change under `dest_root`: modify the file a hunk
  touches, create a file the patch introduces, remove a file it drops. The
  `PatchedFile` and `Hunk` API gives you what you need --
  `is_added_file` / `is_removed_file` / `is_modified_file`, the file's `path`,
  and per hunk the source region (`source_start`, `source_length`,
  `source_lines()`) and the replacement lines (`target_lines()`).
- Return the per-file `report`.

`docs/working_copy.rst` sketches the `apply_patchset_to_dir` helper and the
`PatchSet` API it builds on.

## Checking your work

There are a handful of ordinary cases in `patch_tests/test_apply.py`:

```
python -m pytest patch_tests/test_apply.py -q
```

The `unidiff` package is importable from the repo root, so you can exercise your
implementation directly too. Thanks!
