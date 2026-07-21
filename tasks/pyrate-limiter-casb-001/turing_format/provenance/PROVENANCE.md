# Provenance - pyrate-limiter-casb-001

The task baseline is the upstream PyrateLimiter release **v3.9.0** plus a single
scaffolding commit that adds the unimplemented feature stub, the discoverable
rule doc, and the visible tests. Everything needed to verify this independently
ships in this folder.

## Coordinates

| | |
| --- | --- |
| Upstream repo | https://github.com/vutran1710/PyrateLimiter |
| Upstream license | MIT |
| Upstream tag | v3.9.0 |
| Upstream commit | `8cb467ea54c68368eaf34deef1a6cc38c41218a2` |
| Base commit | `23b4a6e303f4b22e7489cbc4085186f62a815c62` |
| Base tree | `8ba863c85d83e5518aa9e1f41acc7cd60896738b` |
| Scaffolding commit message | `Add bounded limiter stub, state-management doc, and tests (feature unimplemented)` |

## What the scaffolding commit adds

- `pyrate_limiter/bounded_limiter.py` - the `BoundedLimiter` class with a written
  `__init__` and a `try_acquire` that raises `NotImplementedError`.
- `docs/limiter_state_management.md` - the discoverable rule (reclaiming state
  must not change a decision; a key at its limit stays throttled for its window).
- `tests/test_bounded_limiter.py` - the visible tests (single client, rollover,
  independence, weighted requests, memory bound, expired reclamation) with a
  mock clock.
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

`baseline.patch` is the exact diff from the upstream commit to the base commit.

## Verify it yourself

```
bash reconstruct.sh /tmp/prl_recon
```

This clones upstream with LF line endings, checks out the upstream commit,
applies `baseline.patch`, commits with the recorded message, and confirms the
reconstructed tree hash equals `8ba863c85d83e5518aa9e1f41acc7cd60896738b`.

To confirm the shipped working tree matches the reconstruction:

```
diff -rq --exclude=.git ../repo/src /tmp/prl_recon/pyrate_limiter
```

(The shipped `turing_format/repo/src` is the base commit's tree exported with
`git archive`, so it contains no `.git` directory; provenance is what proves it
came from upstream.)
