# Provenance - pyotp-casb-001

The task baseline is the upstream pyotp release **v2.10.0** plus a single
scaffolding commit that adds the unimplemented feature stub, the discoverable
rule doc, and the visible tests. Everything needed to verify this independently
ships in this folder.

## Coordinates

| | |
| --- | --- |
| Upstream repo | https://github.com/pyauth/pyotp |
| Upstream license | MIT |
| Upstream tag | v2.10.0 |
| Upstream commit | `81ed54ac7347fbac522ce9c6bd1bca8e18ad4603` |
| Base commit | `21a8d0cd05c25f97b0cab701e9b83f3f433c09f1` |
| Base tree | `66f05ec1001de327b4ffe5e6e536b1b03de2f33f` |
| Scaffolding commit message | `Add replay guard stub, verification-state doc, and tests (feature unimplemented)` |

## What the scaffolding commit adds

- `src/pyotp/replay_guard.py` - the `ReplayGuard` class with a written
  `__init__` and a `verify` that raises `NotImplementedError`.
- `docs/verification_state.md` - the discoverable rule (single use per RFC 6238
  Section 5.2; a code accepted once must never be accepted again within its
  window; only fully-expired records may be reclaimed).
- `tests/test_replay_guard.py` - the visible tests (valid code accepted once,
  replay rejected in-window, invalid code rejected, per-account independence,
  a fresh code in a new step, the memory bound, expired reclamation) with a
  fixed UTC clock.
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

`baseline.patch` is the exact diff from the upstream commit to the base commit.

## Verify it yourself

```
bash reconstruct.sh /tmp/pyotp_recon
```

This clones upstream with LF line endings, checks out the upstream commit,
applies `baseline.patch`, commits with the recorded message, and confirms the
reconstructed tree hash equals `66f05ec1001de327b4ffe5e6e536b1b03de2f33f`.

To confirm the shipped working tree matches the reconstruction:

```
diff -rq --exclude=.git ../repo/src /tmp/pyotp_recon/pyotp
```

(The shipped `turing_format/repo/src` is the base commit's tree exported with
`git archive`, so it contains no `.git` directory; provenance is what proves it
came from upstream.)
