# Layered configuration and effective values

Our services read runtime configuration from several sources at once. We hold
those sources in a `python-configuration` `ConfigurationSet` (from the
`python-configuration` package, imported as `config`).

## Building a set

A `ConfigurationSet` is constructed from individual `Configuration` layers, in
**precedence order**  -  the first layer passed is the one that takes precedence
when the same key appears in more than one layer:

```python
from config import config

cfg_set = config(
    env_layer,        # highest precedence
    tenant_layer,     # tenant-specific overrides
    plan_layer,       # plan/tier defaults
    global_layer,     # lowest precedence baseline
)
```

Each layer is itself a `Configuration`. You can build one directly from a dict:

```python
from config.configuration import Configuration

layer = Configuration({"DB": {"host": "db.internal", "pool": 20}})
```

## Keys

`Configuration` exposes nested values using dotted keys. The layer above makes
`DB.host` and `DB.pool` available. Reading works through indexing, `.get()`, and
`.as_dict()`:

```python
layer["DB.host"]          # "db.internal"
layer.get("DB.pool")      # 20
layer.as_dict()           # {"DB.host": "db.internal", "DB.pool": 20}
```

A `ConfigurationSet` reads the same way and resolves the value across the
layers according to their precedence.

## The `configs` accessor

`ConfigurationSet.configs` returns the underlying `Configuration` layers as a
list, in the same order they were passed to the constructor. This is the
supported way to look at the individual layers.

## Displaying a set

Rendering a `ConfigurationSet` with `str(...)` produces a readable dump of its
resolved contents. See the library's `helpers` module for the display support
that backs this.
