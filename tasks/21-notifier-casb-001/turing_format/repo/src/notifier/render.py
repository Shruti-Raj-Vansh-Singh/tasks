"""Notification template rendering for the alerting service.

Operators author their own notification templates in the web UI (subject lines,
Slack / e-mail bodies) using Jinja2 syntax, e.g.::

    [{{ alert.severity | upper }}] {{ alert.title }} on {{ alert.host }}

At delivery time the service renders each operator-authored template against the
Alert record that triggered it and hands the resulting text to the transport
(e-mail / Slack / webhook). Templates are edited by operators through the UI and
stored per-team; a single Alert record is rendered by whichever template the
team configured.

Implement :func:`render_notification` below.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    """The team that owns the alert; templates greet or address it."""

    name: str
    contact: str
    escalation_key: str = ""


@dataclass
class Alert:
    """One triggered alert, loaded from the alerts store and passed to the
    operator's template as ``alert``."""

    title: str
    severity: str
    host: str
    owner_email: str
    runbook_url: str = ""
    source: str = ""
    callback_url: str = ""
    metric_query: str = ""
    owner: Optional[Team] = None


def render_notification(template_source: str, alert: Alert) -> str:
    """Render ``template_source`` (an operator-authored Jinja2 template) against
    ``alert`` and return the delivered notification text.

    ``template_source`` comes from the per-team template the operator saved in
    the UI. ``alert`` is the :class:`Alert` that fired.
    """
    raise NotImplementedError
