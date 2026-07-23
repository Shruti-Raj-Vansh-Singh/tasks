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

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from jinja2.sandbox import SandboxedEnvironment


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


# Operator-authored template source is untrusted (any team can save arbitrary
# Jinja2 through the UI) and the rendered text is delivered into HTML-bearing
# transports, so the environment both sandboxes execution and escapes output.
_ENV = SandboxedEnvironment(autoescape=True)

# The only alert fields an operator template may reference. Everything else on
# the record -- notably the signed callback URL and the raw metric query, which
# embed a delivery token and a datasource DSN -- is withheld.
_ALERT_FIELDS = ("title", "severity", "host", "owner_email", "runbook_url", "source")
# The only team fields a template may reference; the escalation key is withheld.
_TEAM_FIELDS = ("name", "contact")


def _view(alert: Alert) -> Dict[str, Any]:
    """A minimised, display-only projection of the alert.

    Only the presentation fields are exposed, and the owning team is flattened
    to its display strings rather than handed through as a live object, so a
    template can render ``{{ alert.owner.name }}`` but cannot reach
    ``alert.owner.escalation_key`` or the record's delivery internals.
    """
    view: Dict[str, Any] = {name: getattr(alert, name) for name in _ALERT_FIELDS}
    if alert.owner is not None:
        view["owner"] = {name: getattr(alert.owner, name) for name in _TEAM_FIELDS}
    return view


def render_notification(template_source: str, alert: Alert) -> str:
    """Render ``template_source`` (an operator-authored Jinja2 template) against
    ``alert`` and return the delivered notification text.

    ``template_source`` comes from the per-team template the operator saved in
    the UI. ``alert`` is the :class:`Alert` that fired.
    """
    template = _ENV.from_string(template_source)
    return template.render(alert=_view(alert))
