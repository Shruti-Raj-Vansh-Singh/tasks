"""Build an audit report of the effective runtime configuration.

Our services layer their configuration from several sources. We use the
``python-configuration`` package's
:class:`~config.configuration_set.ConfigurationSet` to hold the layers: it is
constructed with the layers in *precedence order*, the first-listed layer being
the one that takes precedence when the same key appears in more than one layer.

For example a service might build::

    from config import config
    cfg_set = config(
        env_layer,        # highest precedence
        tenant_layer,     # tenant-specific overrides
        plan_layer,       # plan/tier defaults
        global_layer,     # lowest precedence baseline
    )

Ops wants an *audit report* of what each service instance is actually running:
for every configuration key, the value that is in effect together with the name
of the layer that supplied that effective value. This lets them answer "where
did this setting come from?" during an incident without logging into the box.

:func:`build_effective_report` produces that report.
"""

from typing import Any, Dict, List

from config.configuration_set import ConfigurationSet


def build_effective_report(
    cfg_set: ConfigurationSet,
    layer_names: List[str],
) -> Dict[str, Dict[str, Any]]:
    """Report the effective value and originating layer for every config key.

    Args:
        cfg_set: a :class:`ConfigurationSet` whose layers were passed to its
            constructor in precedence order (first = highest precedence).
        layer_names: the human-readable name of each layer, in the *same order*
            the layers were passed to ``cfg_set`` (``layer_names[i]`` names the
            i-th layer). Same length as the number of layers.

    Returns:
        A dict keyed by configuration key. Each value is a dict with:

            ``"value"``:  the effective value of that key across all layers.
            ``"source"``: the ``layer_names`` entry for the layer that supplied
                          the effective value.

        Every key that appears in any layer must appear exactly once in the
        report, with the value and source that are actually in effect.
    """
    # The individual layers, in precedence order (highest first) -- the same
    # order ``layer_names`` is in, so layers[i] is named layer_names[i].
    layers = list(cfg_set.configs)

    # Flatten each layer once to its dotted-key representation. This is exactly
    # the keyspace the set resolves over: ConfigurationSet.as_dict() merges the
    # layers in reverse precedence order, so a key present in any layer is a key
    # in the set, and the effective value is the one from the highest-precedence
    # layer that defines it.
    layer_dicts = [layer.as_dict() for layer in layers]

    report: Dict[str, Dict[str, Any]] = {}
    for layer_dict, name in zip(layer_dicts, layer_names):
        for key, value in layer_dict.items():
            # First layer (highest precedence) to define a key wins; skip any
            # key already claimed by a higher-precedence layer.
            if key in report:
                continue
            report[key] = {"value": value, "source": name}

    return report
