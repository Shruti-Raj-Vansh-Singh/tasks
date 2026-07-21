# Provenance - bottle-casb-001

The task baseline is the upstream Bottle release **0.13.4** plus a single
scaffolding commit that adds the unimplemented feature stub, the discoverable
rule doc, and the visible tests. Everything needed to verify this independently
ships in this folder.

## Coordinates

| | |
| --- | --- |
| Upstream repo | https://github.com/bottlepy/bottle |
| Upstream license | MIT |
| Upstream tag | 0.13.4 |
| Upstream commit | `18faf70f21ba2a96e92d407b06cc017061215bde` |
| Base commit | `db49b6b0a2ab9b283c2c0f50f7e69117f72cb3dd` |
| Base tree | `e6d6519be6ec217e39d334ef0a47cab8a6e9ad0c` |
| Scaffolding commit message | `Add idempotency store stub, dedup semantics doc, and tests (feature unimplemented)` |

## What the scaffolding commit adds

- `bottle_idempotency.py` - the `IdempotencyStore` class with a written
  `__init__` and a `process` method that raises `NotImplementedError`.
- `docs/request_deduplication.rst` - the discoverable rule (an idempotency key
  identifies one specific request; a reused key with a different request must be
  rejected, not served the prior result).
- `test/test_idempotency.py` - the visible tests (first call, genuine retry,
  distinct keys, result passthrough).
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

`baseline.patch` is the exact diff from the upstream commit to the base commit.

## Verify it yourself

```
bash reconstruct.sh /tmp/bottle_recon
```

This clones upstream with LF line endings, checks out the upstream commit,
applies `baseline.patch`, commits with the recorded message, and confirms the
reconstructed tree hash equals `e6d6519be6ec217e39d334ef0a47cab8a6e9ad0c`.

To confirm the shipped working tree matches the reconstruction:

```
diff -rq --exclude=.git ../repo/src /tmp/bottle_recon/bottle
```

(The shipped `turing_format/repo/src` is the base commit's tree exported with
`git archive`, so it contains no `.git` directory; provenance is what proves it
came from upstream.)
