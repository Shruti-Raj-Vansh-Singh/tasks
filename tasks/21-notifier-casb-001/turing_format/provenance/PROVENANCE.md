# Provenance

This task's baseline is Jinja2 `3.1.6` plus one scaffolding commit.

- Upstream repo: `https://github.com/pallets/jinja`
- Upstream license: BSD-3-Clause
- Upstream tag: `3.1.6`
- Upstream commit: `15206881c006c79667fe5154fe80c01c65410679`
- Base commit: `197bd3f6f75e002d192453a83ef9dd0970247486`
- Base tree: `0e9d3472fc2017af63955dcd231c0e6f5af5e562`
- Scaffolding commit message:
  `Add operator notification template rendering stub, ticket, and visible tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds five
new files and modifies no upstream source:

- `src/notifier/render.py` - the `Alert` dataclass and the unimplemented
  `render_notification(template_source, alert)` (raises `NotImplementedError`).
- `src/notifier/__init__.py` - a new `notifier` package marker.
- `NOTIFY_TASK.md` - the agent prompt.
- `notifier_tests/test_render.py` - the visible tests (benign operator templates:
  field interpolation, the `upper` filter, the `default` filter).
- `notifier_tests/__init__.py` - the test package marker.

jinja2 is pure Python and imports directly from the `src/` checkout, so no build
step or generated version file is needed to run the notifier module or its tests.

The visible tests live in a top-level `notifier_tests/` directory rather than
under jinja2's own `tests/` so the notifier suite runs on its own with only
pytest, independent of the library's large test fixture set.

## Verify

```bash
bash reconstruct.sh /tmp/jn_recon
# clones upstream at the tag, applies baseline.patch, commits with the same
# message, and asserts the reconstructed HEAD^{tree} == 0e9d3472...

diff -rq --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache \
  ../repo /tmp/jn_recon/jinja
# expected: no differences. The shipped repo/ is the reconstructed base tree
# verbatim (NOTIFY_TASK.md is present inside the checkout, exactly as
# reconstructed).
```

Note on Windows checkouts: two upstream files
(`.devcontainer/on-create-command.sh` and `scripts/generate_identifier_pattern.py`)
are mode `100755` (executable) in git. A Windows filesystem cannot represent that
bit, so a `repo/` checked out on Windows is byte-identical in content but differs
in those two mode bits. `reconstruct.sh` and the harbor Docker image run on a
POSIX filesystem and reproduce the exact base tree `0e9d3472...`, which is the
authoritative check.
