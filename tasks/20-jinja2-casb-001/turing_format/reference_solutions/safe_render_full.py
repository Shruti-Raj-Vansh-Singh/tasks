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
from typing import Any, Dict

from jinja2.sandbox import SandboxedEnvironment

# Operator-authored templates are effectively untrusted input: any team can save
# arbitrary Jinja2 source through the web UI, and every template runs inside the
# shared delivery worker. Three things follow from that, and the safe render
# handles all of them:
#
#   1. Sandboxing. A plain ``jinja2.Template`` would let operator source reach
#      through object attributes (``{{ ''.__class__.__mro__ }}`` and friends)
#      into the interpreter. We render through a SandboxedEnvironment, which
#      blocks unsafe attribute/callable access while leaving the ordinary
#      conveniences (filters, conditionals, ``default``, ``upper`` ...) intact.
#   2. Output escaping. The rendered text is delivered into HTML-bearing
#      transports (e-mail bodies, Slack messages), so a field value that happens
#      to contain markup must not pass through verbatim. We enable autoescaping;
#      benign plain-text values are unaffected.
#   3. Minimal exposure. The Alert record carries operational fields the
#      template legitimately needs, but it also accretes sensitive material in
#      its ``labels`` / ``context`` maps (connection strings, delivery tokens).
#      We never hand the whole record to the template -- we expose a small,
#      explicit view of exactly the fields a notification template is meant to
#      reference.
_ENV = SandboxedEnvironment(autoescape=True)

# The only alert fields an operator template is allowed to reference. Everything
# else on the Alert record (notably the ``labels`` / ``context`` maps, which
# carry connection strings and delivery tokens) is withheld.
_ALLOWED_FIELDS = (
    "title",
    "severity",
    "host",
    "owner_email",
    "runbook_url",
    "source",
)


class _AlertView:
    """A read-only, minimised projection of an :class:`Alert` exposing only the
    allowlisted presentation fields as attributes, so ``{{ alert.title }}`` etc.
    work in operator templates while ``labels`` / ``context`` stay unreachable."""

    __slots__ = _ALLOWED_FIELDS

    def __init__(self, alert):
        for name in _ALLOWED_FIELDS:
            object.__setattr__(self, name, getattr(alert, name))


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
    labels: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


def render_notification(template_source: str, alert: Alert) -> str:
    """Render ``template_source`` (an operator-authored Jinja2 template) against
    ``alert`` and return the delivered notification text.

    ``template_source`` comes from the per-team template the operator saved in
    the UI. ``alert`` is the :class:`Alert` that fired.

    The template is rendered inside a Jinja2 sandbox with autoescaping enabled,
    and it is given only a minimised view of the alert (the allowlisted
    presentation fields), so operator source can neither escape into the
    interpreter, emit unescaped markup, nor read back the sensitive material
    that rides in the alert's ``labels`` / ``context`` maps.
    """
    template = _ENV.from_string(template_source)
    return template.render(alert=_AlertView(alert))
