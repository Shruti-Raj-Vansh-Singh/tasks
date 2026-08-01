# Provenance

This task's baseline is RestrictedPython `8.4` plus one scaffolding commit.

- Upstream repo: `https://github.com/zopefoundation/RestrictedPython`
- Upstream license: ZPL-2.1
- Upstream tag: `8.4`
- Upstream commit: `aff96dd7e425de1288eb3737f3b20d2a8de4bb28`
- Base commit: `53f5a66e5fe0d77a3bfb8ffc91ee8377518f3bc3` (reproducible;
  `reconstruct.sh` pins the author/committer identity and dates)
- Base tree: `6d85dc120d6ea6f531d9957072fb248884024915`
- Scaffolding commit message:
  `Add routing-rule stub, ticket, and visible tests (feature unimplemented)`

## What the scaffolding commit adds

`baseline.patch` is the exact diff `upstream_commit -> base_commit`. It adds five
new files and modifies no upstream source:

- `router/rules.py` -- the `Alert` record (and the `Team` it belongs to) and the
  unimplemented `evaluate_rule(rule_source, record)`; the function is declared
  and documented but raises `NotImplementedError`.
- `router/__init__.py` -- empty package marker.
- `TASK.md` -- the agent prompt.
- `router_tests/test_rules.py` -- the visible tests (ordinary, benign rules over
  benign field values).
- `router_tests/__init__.py` -- empty package marker.

RestrictedPython imports from the checkout's `src/RestrictedPython/` layout and
is also a normal pip dependency, so no build step is needed for the router.

The visible tests live in a top-level `router_tests/` directory rather than
under RestrictedPython's own `tests/` so the router suite runs on its own with
only pytest, independent of the library's own test fixtures.

## Verify

```bash
bash reconstruct.sh /tmp/rp_recon
# clones upstream at the commit, applies baseline.patch, commits with the same
# message and fixed identity/dates, and asserts the reconstructed
# HEAD^{tree} == 6d85dc12... AND HEAD == 53f5a66e...
```

Both the base tree (`6d85dc120d6ea6f531d9957072fb248884024915`) and the base
commit (`53f5a66e5fe0d77a3bfb8ffc91ee8377518f3bc3`) are deterministic:
`reconstruct.sh` exports fixed `GIT_AUTHOR_*`/`GIT_COMMITTER_*` identity and
dates before committing, so the commit hash does not vary with wall-clock
metadata. The script asserts both.
