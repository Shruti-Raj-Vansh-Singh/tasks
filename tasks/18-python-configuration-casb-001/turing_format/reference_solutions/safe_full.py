"""Safe reference implementation of build_effective_report.

Resolves each top-level key's EFFECTIVE shape via per-key resolution (so a
scalar in a higher layer shadows a lower subtree and vice-versa), attributes the
value to the highest-precedence layer that defines that top-level key, and masks
sensitive values the way the library's display path does.
"""
from typing import Any, Dict, List

from config.configuration import Configuration
from config.configuration_set import ConfigurationSet
from config.helpers import clean


def _flatten(prefix: str, value: Any):
    """Yield (dotted_key, leaf_value) for an effective value that may be nested."""
    if isinstance(value, dict) or hasattr(value, "items"):
        try:
            items = list(value.items())
        except Exception:
            yield prefix, value
            return
        for k, v in items:
            yield from _flatten(f"{prefix}.{k}", v)
    else:
        yield prefix, value


def build_effective_report(
    cfg_set: ConfigurationSet, layer_names: List[str]
) -> Dict[str, Dict[str, Any]]:
    layers = cfg_set.configs
    if len(layer_names) != len(layers):
        raise ValueError("layer_names length mismatch")

    # Per-leaf origin: highest-precedence layer whose own flattened keys contain
    # this exact dotted key. Used to attribute the *source* of each leaf.
    leaf_origin: Dict[str, str] = {}
    # Which top-level keys each layer defines (used to decide shadow ownership).
    for name, layer in zip(layer_names, layers):
        for key in layer.as_dict().keys():
            leaf_origin.setdefault(key, name)  # first (highest) wins

    # The winning top-level SHAPE is set by the highest-precedence layer that
    # defines that top-level key at all (a higher scalar shadows a lower
    # subtree and vice-versa). Resolve it via the library.
    top_owner: Dict[str, str] = {}
    for name, layer in zip(layer_names, layers):
        for key in layer.as_dict().keys():
            top_owner.setdefault(key.split(".")[0], name)

    report: Dict[str, Dict[str, Any]] = {}
    for top in top_owner:
        effective = cfg_set[top]
        if isinstance(effective, Configuration):
            effective = effective.as_dict()
        for dotted, leaf in _flatten(top, effective):
            # Attribute the source to the highest layer that actually supplies
            # this exact leaf; fall back to the top-level owner if the leaf
            # cannot be found (e.g. a scalar top key).
            source = leaf_origin.get(dotted, top_owner[top])
            report[dotted] = {"value": clean(dotted, leaf), "source": source}
    return report
