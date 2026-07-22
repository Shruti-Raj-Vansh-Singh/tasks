"""Effective-config audit report builder."""
from typing import Any, Dict, List

from config.configuration_set import ConfigurationSet


def build_effective_report(cfg_set: "ConfigurationSet", layer_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """Build an effective-configuration audit report.

    Args:
        cfg_set: a ConfigurationSet holding the config layers, passed to its
            constructor in precedence order (first-listed layer wins on conflict).
        layer_names: names of the layers, in the same order the layers were
            passed to cfg_set.

    Returns:
        A dict keyed by every configuration key that appears in any layer. Each
        entry is ``{"value": <effective value>, "source": <layer name>}`` where
        "value" is the value the service actually sees for that key and "source"
        is the layer_names entry for the layer that supplied it. Every key that
        appears anywhere appears exactly once.
    """
    raise NotImplementedError
