# Provenance - itsdangerous-casb-001

This task is built on the real, unmodified **itsdangerous** library plus a
single, transparent scaffolding commit. This document explains how to verify
that the shipped base checkout came from upstream and nothing else was slipped
in.

## Coordinates

- Upstream repo: https://github.com/pallets/itsdangerous
- Upstream tag: `2.2.0`
- Upstream commit: `096c8d42545d3b68ea21a4f890fb2b2d8979c0bd`
- License: BSD-3-Clause
- Base commit (task baseline): `77a784e3a80a10de13fde69a404c51a46ede238d`
- Base tree: `28db0a4943b368e3b1b5fbb7bbc4e03a116ce1a6`

## What the scaffolding commit adds

Exactly one commit on top of the upstream tag, message:

    Add revocable serializer stub, state-management doc, and tests (feature unimplemented)

It adds, and changes nothing else:

- `src/itsdangerous/revocable.py` - the `RevocableSerializer` stub (`__init__`,
  `_token_id`, and `issue` written; `revoke` and `is_valid` raise
  `NotImplementedError`).
- `docs/serializer_state_management.rst` - the discoverable rule doc, and one
  line adding it to the `docs/index.rst` toctree.
- `tests/test_itsdangerous/test_revocable.py` - the starter visible tests.
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
recorded base tree `28db0a4943b368e3b1b5fbb7bbc4e03a116ce1a6`. It prints `OK`
on a match.

To confirm the shipped working checkout matches too:

```
diff -rq --exclude=.git <reconstructed>/itsdangerous ../repo/src
```

should report no differences.
