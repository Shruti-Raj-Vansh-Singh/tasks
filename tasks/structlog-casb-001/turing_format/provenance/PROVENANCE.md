# Provenance

This task's baseline is structlog `26.1.0` plus one scaffolding commit.

- Upstream repo: `https://github.com/hynek/structlog`
- Upstream license: MIT OR Apache-2.0
- Upstream tag: `26.1.0`
- Upstream commit: `8174a86a2f14b5bd295eded733ff5fffc12aa173`
- Base commit: `f94242a13b146554810655819a861bbfc8a851ba`
- Base tree: `6a371f6bea837fb115c8ef52a84c06db28d84f2e`
- Scaffolding commit message:
  `Add single-line audit renderer stub, format doc, and tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds only:

- `src/structlog/_audit.py` - the unimplemented `AuditLineRenderer` stub
  (`render()` raises `NotImplementedError`) plus the `render_audit_line` wrapper.
- `src/structlog/__init__.py` - two lines exporting `AuditLineRenderer` and
  `render_audit_line` (and their entries in `__all__`).
- `docs/audit_log_format.md` - the discoverable one-record-per-line rule page.
- `tests/test_audit.py` - the visible tests.
- `.gitattributes` - `* text=auto eol=lf` to pin line endings.

No existing structlog source is modified.

## Verify

```bash
bash reconstruct.sh /tmp/sl_recon
# clones upstream at the tag, applies baseline.patch, commits with the same
# message, and asserts the reconstructed HEAD^{tree} == 6a371f6b...

diff -rq --exclude=.git ../repo/src /tmp/sl_recon/structlog
# expected: no differences (the shipped repo/src is byte-identical to the
# reconstructed base tree; both are LF on disk).
```
