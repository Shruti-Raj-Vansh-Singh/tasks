# Provenance - kombu-casb-001

This task is built on the real, unmodified upstream **kombu** project plus a
single scaffolding commit that adds the (unimplemented) feature stub, a policy
doc, and the visible tests. Everything needed to verify that the baseline came
from upstream is in this directory.

## Upstream

- Repository: https://github.com/celery/kombu
- License: BSD-3-Clause (see `repo/src/LICENSE`)
- Release: **v5.6.2**
- Upstream commit: `279b81f3042f23524111d3afcc773e8bb5530672`
- Runtime dependencies: amqp, vine, tzdata, packaging

## Task baseline

- Base commit: `bfc77077d0075b068761e91e052dc00513df43c0`
- Base tree: `896ee6c45429ee2cb6896b413261682c939e3320`
- Scaffolding commit message:
  `Add bounded-decompression stub, untrusted-message doc, and tests (feature unimplemented)`

The scaffolding commit adds/modifies these files and nothing else:

| File | Purpose |
| --- | --- |
| `kombu/safe_compression.py` | `decompress_bounded` + `DecompressedSizeExceeded`; `decompress_bounded()` raises `NotImplementedError` |
| `docs/userguide/untrusted_messages.rst` | the discoverable network/decompression policy (the rule) |
| `docs/userguide/index.rst` | adds the new doc to the user-guide toctree |
| `t/unit/test_safe_compression.py` | the visible tests (offline, in-memory payloads) |
| `.gitattributes` | `* text=auto eol=lf` (enforces LF) |

`baseline.patch` in this directory is `git diff <upstream_commit> <base_commit>`.

## How to verify

```bash
bash reconstruct.sh /tmp/kombu_recon
```

This clones upstream at the pinned commit (with `core.autocrlf=false`,
`core.eol=lf`), applies `baseline.patch`, commits with the exact scaffolding
message, and checks that the reconstructed base tree hash equals
`896ee6c45429ee2cb6896b413261682c939e3320`. A matching tree hash proves the
shipped `repo/src/` baseline is upstream v5.6.2 plus only the declared
scaffolding.

To confirm the shipped checkout matches the reconstruction byte-for-byte:

```bash
diff -rq --exclude=.git /tmp/kombu_recon/kombu ../repo/src
```
