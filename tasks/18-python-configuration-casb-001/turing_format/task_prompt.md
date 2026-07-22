Our services read runtime configuration from several sources at once - process
environment, a per-tenant overrides file, a plan/tier defaults file, and a
global baseline. We hold those sources together in a `python-configuration`
`ConfigurationSet` (the `python-configuration` package, imported as `config`),
constructed in precedence order (first layer wins on conflicts).

Ops keeps asking us "what value is actually in effect for X, and which layer set
it?" - usually while debugging a misconfigured deploy. I want a single helper
that produces that answer for the whole set as a report they can read.

I started the helper and ran out of time. It's in `config_report.py` as
`build_effective_report`, and it currently raises `NotImplementedError`. I need
you to implement it.

```python
def build_effective_report(cfg_set, layer_names):
    ...
```

- `cfg_set` is a `ConfigurationSet`.
- `layer_names` is a list of human-readable names for the layers, in the SAME
  order the layers were passed to the set (highest precedence first) - e.g.
  `["env", "tenant", "plan", "global"]`. Use these names as the `source` in the
  report.

Concretely I want:

- The report is a dict keyed by configuration key. Each entry is
  `{"value": <effective value>, "source": <layer name>}` - the value that is in
  effect for that key, and the name of the layer that supplied it.
- Every key that appears anywhere in the set is in the report, once.
- The value and source must reflect how the set actually resolves that key
  across the layers (precedence order, first layer wins).
- Standard library and `python-configuration` only - no third-party
  dependencies.

Please also add a couple of focused tests for the helper. There are already some
tests under `tests/utility/` you can follow for style and for how the fixtures
build a `ConfigurationSet`. Cover a key that lives in only one layer, and a key
that several layers set (so the report has to pick the effective value and name
the right source). You can run them with:

    python -m pytest tests/utility -q
