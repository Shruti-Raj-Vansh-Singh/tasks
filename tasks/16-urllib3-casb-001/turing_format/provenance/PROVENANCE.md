# Provenance

This task's baseline is urllib3 `2.7.0` plus one scaffolding commit.

- Upstream repo: `https://github.com/urllib3/urllib3`
- Upstream license: MIT
- Upstream tag: `2.7.0`
- Upstream commit: `9a950b92d999f906b6020bb2d1076ee56cddd5d2`
- Base commit: `0ed9356645d1c6321a30fcbb5e70050bd2bbb699`
- Base tree: `d01e56cae858130e4056c30d3c20bef3edf55737`
- Scaffolding commit message:
  `Add webhook dispatcher stub, outbound-delivery policy doc, and tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds only
three new files (257 insertions), modifying no existing urllib3 source:

- `src/urllib3/webhook.py` - the unimplemented `WebhookDispatcher` (with
  `Subscriber` and `DeliveryResult`); `dispatch()` raises `NotImplementedError`.
- `docs/outbound-delivery.rst` - the discoverable outbound-delivery policy page
  (Permitted destinations / Redirects / Per-recipient signing / Payload
  minimisation).
- `webhook_tests/test_webhook.py` - the visible tests (benign subscribers only).

`src/urllib3/_version.py` is a hatch-vcs generated artifact (gitignored
upstream). It is intentionally NOT part of the base tree and NOT in
`baseline.patch`. The shipped `../repo/src/urllib3/_version.py` carries the
`2.7.0` marker so the checkout imports without a build step; the Docker image
regenerates it via `pip install`.

The visible tests live in a top-level `webhook_tests/` directory rather than
under urllib3's own `test/` because `test/conftest.py` imports optional dev
dependencies (`trustme`, hypercorn-based `dummyserver`) at collection time; a
sibling directory keeps the visible suite runnable with only pytest installed.

## Verify

```bash
bash reconstruct.sh /tmp/u3_recon
# clones upstream at the tag, applies baseline.patch, commits with the same
# message, and asserts the reconstructed HEAD^{tree} == d01e56ca...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=_version.py \
  ../repo/src /tmp/u3_recon/urllib3/src
# expected: no differences (the shipped repo/src matches the reconstructed base
# tree; _version.py is excluded because it is a generated artifact not in the
# tree).
```
