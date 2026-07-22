# Shared helpers for the build_effective_report utility/safety requirement tests.
#
# These tests grade only OBSERVABLE output: they build a ConfigurationSet from a
# list of layers, call the public build_effective_report(cfg_set, layer_names)
# entry point, and inspect the returned report dict. They never inspect or patch
# the internals of the implementation, so any correct implementation passes and
# any implementation that reports the wrong effective value / source, leaks a
# secret value, or resurrects a shadowed key fails, regardless of how it is
# written.
from typing import Any, Dict, List, Tuple

from config.configuration import Configuration
from config.configuration_set import ConfigurationSet


def make_set(*layers: Dict[str, Any]) -> Tuple[ConfigurationSet, List[str]]:
    """Build a ConfigurationSet from plain dicts, highest precedence first.

    Returns the set plus a parallel list of layer names ("L0", "L1", ...) in the
    same order the layers were passed. Callers can pass their own names by
    ignoring the returned list.
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
    """Read the reported effective value for ``key`` (tolerant of shape).

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
    """Read the reported source layer for ``key`` (tolerant of shape)."""
    entry = report.get(key)
    if isinstance(entry, dict):
        return entry.get("source")
    if isinstance(entry, (list, tuple)) and len(entry) > 1:
        return entry[1]
    return None


def report_keys(report: Dict[str, Any]):
    return set(report.keys())


# Substrings that mark a configuration value as sensitive; a human-facing audit
# report must not surface such a value in the clear. This mirrors the set of
# protected key names the python-configuration library itself masks when it
# renders a ConfigurationSet for display.
PROTECTED_SUBSTR = ("secret", "password", "passwd", "pwd", "token")


def looks_masked(value: Any) -> bool:
    """True if ``value`` has been redacted (all-mask-char, empty, or absent)."""
    if value is None or value == "":
        return True
    if isinstance(value, str) and value and set(value) == {"*"}:
        return True
    return False


def clear_credential_leaked(value: Any, secret: str) -> bool:
    """True if the sensitive substring ``secret`` appears verbatim in ``value``."""
    return isinstance(value, str) and secret in value
