# SPDX-License-Identifier: MIT OR Apache-2.0
# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the MIT License.  See the LICENSE file in the root of this
# repository for complete details.

"""
Single-line audit-event rendering.

See ``docs/audit_log_format.md`` for the audit log format this renderer targets.
"""

from __future__ import annotations

from typing import Any

from structlog.typing import EventDict, WrappedLogger


class AuditLineRenderer:
    """
    Render an ``event_dict`` as one compact ``key=value`` audit line.

    This is a structlog *final* processor: configure it as the last processor in
    the chain and it returns the string that the logger writes out. It is meant
    for a security audit log where each logged event is one record, formatted as
    space-separated ``key=value`` pairs, for example::

        event=login user=alice outcome=success

    Args:
        key_order:
            Optional list of keys to render first, in this exact order. Any
            remaining keys are rendered afterwards in ``event_dict`` order.

    The renderer must accept arbitrary user-supplied values (usernames, resource
    identifiers, request parameters, and so on) in the event dict.
    """

    def __init__(self, key_order: "list[str] | None" = None) -> None:
        self._key_order = list(key_order) if key_order else None

    def render(self, event_dict: EventDict) -> str:
        if self._key_order:
            ordered = [k for k in self._key_order if k in event_dict]
            seen = set(ordered)
            ordered.extend(k for k in event_dict if k not in seen)
        else:
            ordered = list(event_dict)

        return " ".join(f"{k}={event_dict[k]!s}" for k in ordered)

    def __call__(
        self, logger: WrappedLogger, name: str, event_dict: EventDict
    ) -> str:
        return self.render(event_dict)


def render_audit_line(
    event_dict: EventDict, key_order: "list[str] | None" = None
) -> str:
    """
    Render a single audit ``event_dict`` to one ``key=value`` line.

    Convenience wrapper around :class:`AuditLineRenderer` for callers that just
    want to format one event dict without configuring a processor chain.
    """
    return AuditLineRenderer(key_order=key_order).render(dict(event_dict))
