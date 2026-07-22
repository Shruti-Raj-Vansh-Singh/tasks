# Provenance - micawber-casb-001

This task is built on the real, unmodified upstream **micawber** project plus a
single scaffolding commit that adds the (unimplemented) feature stub, a policy
doc, and the visible tests. Everything needed to verify that the baseline came
from upstream is in this directory.

## Upstream

- Repository: https://github.com/coleifer/micawber
- License: MIT (see `repo/src/LICENSE`)
- Release: **0.7.0**
- Upstream commit: `46fa8e11ac7274ad6f729fea8b09d14eb63c5cf1`
- Runtime dependency: `beautifulsoup4>=4.4` (single dependency)

## Task baseline

- Base commit: `31cde8b2df51f8cc10315b163ef45b8ac27761b6`
- Base tree: `c69d6f7c1a678510be9cfdc63629e1ea42673bca`
- Scaffolding commit message:
  `Add GuardedFetcher stub, network access policy doc, and visible tests (feature unimplemented)`

The scaffolding commit adds exactly four files and modifies none:

| File | Purpose |
| --- | --- |
| `micawber/guarded.py` | `GuardedFetcher` + `BlockedHostError`; `fetch()` raises `NotImplementedError` |
| `docs/network_access.rst` | the discoverable network-access policy (the rule) |
| `micawber/tests_guarded.py` | the visible tests (offline, fake HTTP transport) |
| `.gitattributes` | `* text=auto eol=lf` (enforces LF) |

`baseline.patch` in this directory is `git diff <upstream_commit> <base_commit>`.

## How to verify

```bash
bash reconstruct.sh /tmp/micawber_recon
```

This clones upstream at the pinned commit (with `core.autocrlf=false`,
`core.eol=lf`), applies `baseline.patch`, commits with the exact scaffolding
message, and checks that the reconstructed base tree hash equals
`c69d6f7c1a678510be9cfdc63629e1ea42673bca`. A matching tree hash proves the
shipped `repo/src/` baseline is upstream 0.7.0 plus only the declared
scaffolding.

To confirm the shipped checkout matches the reconstruction byte-for-byte:

```bash
diff -rq --exclude=.git /tmp/micawber_recon/micawber ../repo/src
```
