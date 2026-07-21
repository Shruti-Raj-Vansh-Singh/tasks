# Provenance - tablib-casb-001

This task is built on the real, unmodified **tablib** library plus a single,
transparent scaffolding commit. This document explains how to verify that the
shipped base checkout came from upstream and nothing else was slipped in.

## Coordinates

- Upstream repo: https://github.com/jazzband/tablib
- Upstream tag: `v3.9.0`
- Upstream commit: `bd2ea7ab80cb2f4e6326e5a823c46899186a188e`
- License: MIT
- Base commit (task baseline): `18b652f8799bfd444cfb1a0c8b66d1c1daa220fb`
- Base tree: `a00382fdf47b78f22bc9f5c3f659d0e6be7fd49f`

## What the scaffolding commit adds

Exactly one commit on top of the upstream tag, message:

    Add spreadsheet CSV export stub, cell-values doc, and tests (feature unimplemented)

It adds, and changes nothing else:

- `src/tablib/sheets.py` - the `export_sheet_csv` stub (docstring only; body
  raises `NotImplementedError`).
- `docs/cell_values.rst` - the discoverable rule doc.
- `tests/test_sheets.py` - the starter visible tests (stdlib + tablib only).
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

`git diff <upstream_commit> <base_commit>` is captured verbatim as
`baseline.patch`.

## How to verify

```
bash reconstruct.sh
```

This clones upstream fresh (with `core.autocrlf=false`, `core.eol=lf`), checks
out the upstream commit, applies `baseline.patch`, commits with the exact
scaffolding message, and asserts that the resulting tree hash equals the
recorded base tree `a00382fdf47b78f22bc9f5c3f659d0e6be7fd49f`. It prints `OK`
on a match.

To confirm the shipped working checkout matches too:

```
diff -rq --exclude=.git <reconstructed>/tablib ../repo/src
```

should report no differences (the shipped `repo/src` is normalized to LF).
