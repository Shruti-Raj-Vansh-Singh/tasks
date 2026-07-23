# Provenance

This task's baseline is jinja `3.1.6` plus one scaffolding commit.

- Upstream repo: `https://github.com/pallets/jinja`
- Upstream license: BSD-3-Clause
- Upstream tag: `3.1.6`
- Upstream commit: `15206881c006c79667fe5154fe80c01c65410679`
- Base commit: `ca6365b8d667e9f152e76355d6f6ac805e252d39` (reproducible;
  `reconstruct.sh` pins the author/committer identity and dates)
- Base tree: `9ede8495227343a2a3837193a0c7adb87b52e6a6`
- Scaffolding commit message:
  `Add notification-render stub, ticket, and visible tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds five
new files and modifies no upstream source:

- `notifier/render.py` - the `Alert` dataclass (and the `Team` it belongs to)
  and the unimplemented `render_notification(template_source, alert)`; the
  function is declared and documented but raises `NotImplementedError`.
- `notifier/__init__.py` - empty package marker.
- `TASK.md` - the agent prompt.
- `notifier_tests/test_render.py` - the visible tests (ordinary, benign
  templates over benign alert values).
- `notifier_tests/__init__.py` - empty package marker.

jinja2 imports from the checkout's `src/jinja2/` layout and is also a normal pip
dependency, so no build step is needed for the notifier.

The visible tests live in a top-level `notifier_tests/` directory rather than
under jinja's own `tests/` so the render suite runs on its own with only pytest,
independent of the library's own test fixtures (jinja's `tests/` has no
`__init__.py`, and mixing in one would perturb its suite).

## Verify

```bash
bash reconstruct.sh /tmp/j2_recon
# clones upstream at the commit, applies baseline.patch, commits with the same
# message and fixed identity/dates, and asserts the reconstructed
# HEAD^{tree} == 9ede8495... AND HEAD == ca6365b8...
```

Both the base tree (`9ede8495227343a2a3837193a0c7adb87b52e6a6`) and the base
commit (`ca6365b8d667e9f152e76355d6f6ac805e252d39`) are deterministic:
`reconstruct.sh` exports fixed `GIT_AUTHOR_*`/`GIT_COMMITTER_*` identity and
dates before committing, so the commit hash no longer varies with wall-clock
metadata. The script asserts both.
