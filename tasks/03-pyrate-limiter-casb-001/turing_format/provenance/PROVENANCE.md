# Provenance - pyrate-limiter-casb-001

The task baseline is the upstream PyrateLimiter release **v3.9.0** plus a single
scaffolding commit that adds the unimplemented feature stubs, the discoverable
rule doc, and the visible tests. Everything needed to verify this independently
ships in this folder; the online path is optional.

## Coordinates

| | |
| --- | --- |
| Upstream repo | https://github.com/vutran1710/PyrateLimiter |
| Upstream license | MIT |
| Upstream tag | v3.9.0 |
| Upstream commit | `8cb467ea54c68368eaf34deef1a6cc38c41218a2` |
| Upstream tree | `a30e80966ee1ab886cc7536ef35654fe4438b4d9` |
| Base commit | `ea8d3195a38ce1489aec0a5e3ace8f483842559e` |
| Base tree | `59c59fc99c8e553aa9982c6adf228b390ffb683d` |
| Scaffolding commit message | `pyrate-limiter-casb-001 baseline: BoundedLimiter stub, state-management doc, visible tests` |
| Commit identity | `Task Author <author@example.com>` |
| Commit timestamps | `2026-08-11T00:00:00+00:00` (author and committer) |

The fixed identity and timestamps are what make the base *commit* hash - not just
the tree - reproducible.

## What the scaffolding commit adds

Exactly four files, 394 added lines, no upstream file modified or deleted
(`upstream_delta.patch --stat`):

- `pyrate_limiter/bounded_limiter.py` - the `BoundedLimiter` class with a written
  `__init__` and two methods that raise `NotImplementedError`: `try_acquire` and
  `try_acquire_request`.
- `docs/limiter_state_management.md` - the discoverable rules: reclaiming state
  must not change a decision (S1); reclamation must actually release state,
  including for an active key (S3); the value a limit is keyed on must be one the
  requester cannot select, with `X-Forwarded-For`'s append-at-the-end structure
  spelled out (S2); identities from different credential kinds must not collide
  (S4).
- `tests/test_bounded_limiter.py` - the 13 visible tests with a mock clock.
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

## The two patches

| File | From | To | Used by |
| --- | --- | --- | --- |
| `baseline.patch` | empty tree | base tree | `reconstruct.sh` (offline), verifier `Dockerfile` |
| `upstream_delta.patch` | upstream commit | base tree | `reconstruct.sh --upstream` |

`baseline.patch` is a binary-safe full-tree creation patch, so the verifier image
builds with no network access at all. `upstream_delta.patch` is the small diff
that proves the relationship to upstream; it is 4 files and is readable by hand.

## Verify it yourself

```
bash reconstruct.sh /tmp/prl_recon                # offline, no network
bash reconstruct.sh --upstream /tmp/prl_recon_up  # clones upstream
```

Each asserts the reconstructed tree hash equals
`59c59fc99c8e553aa9982c6adf228b390ffb683d`; the offline path additionally asserts
the commit hash. (In upstream mode the baseline commit has upstream history as
its parent, so its hash differs by construction - the tree is what identifies the
baseline.)

To confirm the shipped working tree matches the reconstruction:

```
diff -rq --exclude=.git ../repo/src /tmp/prl_recon/pyrate_limiter
```

The shipped `turing_format/repo/src` is the complete vendored baseline tree
(no `.git` directory); provenance is what proves it came from upstream.

## Verified

2026-08-11, on host: offline mode reproduces tree **and** commit; upstream mode
reproduces the tree; `diff -rq` against `repo/src` is empty for both.

2026-08-11, in a Linux container: the same offline reconstruction steps the
`Dockerfile` runs (`git init`, `git apply --binary baseline.patch`, commit with
the fixed identity and timestamps) reproduce tree
`59c59fc99c8e553aa9982c6adf228b390ffb683d`, and the build-time hash assertion
passes. This is the check that matters for line-ending fidelity, since the
authoring host is Windows and the verifier runs on Linux.
