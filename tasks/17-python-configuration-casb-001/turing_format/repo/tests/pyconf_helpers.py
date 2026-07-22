# Shared helpers for the build_effective_report tests.
#
# These tests grade only OBSERVABLE output: they build a ConfigurationSet from a
# list of layers, call the public build_effective_report(cfg_set, layer_names)
# entry point, and inspect the returned report dict. They never inspect or patch
# the internals of the implementation, so any correct implementation passes
# regardless of how it is written.
from typing import Any, Dict, List, Tuple

from config.configuration import Configuration
from config.configuration_set import ConfigurationSet


def make_set(*layers: Dict[str, Any]) -> Tuple[ConfigurationSet, List[str]]:
    """Build a ConfigurationSet from plain dicts, highest precedence first.

    Returns the set plus a parallel list of layer names ("L0", "L1", ...) in the
    same order the layers were passed.
    """
    configs = [Configuration(d) for d in layers]
    names = ["L%d" % i for i in range(len(layers))]
    return ConfigurationSet(*configs), names


def make_named_set(named_layers: List[Tuple[str, Dict[str, Any]]]):
    """Build a ConfigurationSet from (name, dict) pairs, highest precedence first."""
    names = [n for n, _ in named_layers]
    configs = [Configuration(d) for _, d in named_layers]
    return ConfigurationSet(*configs), names


def entry_value(report: Dict[str, Any], key: str) -> Any:
    """Read the reported value for ``key`` (tolerant of entry shape).

    Accepts an entry that is a {"value","source"} dict, a (value, source) tuple,
    or a bare value.
    """
    entry = report.get(key)
    if isinstance(entry, dict):
        return entry.get("value")
    if isinstance(entry, (list, tuple)) and entry:
        return entry[0]
    return entry


def entry_source(report: Dict[str, Any], key: str) -> Any:
    """Read the reported source layer for ``key`` (tolerant of entry shape)."""
    entry = report.get(key)
    if isinstance(entry, dict):
        return entry.get("source")
    if isinstance(entry, (list, tuple)) and len(entry) > 1:
        return entry[1]
    return None


def report_keys(report: Dict[str, Any]):
    return set(report.keys())
