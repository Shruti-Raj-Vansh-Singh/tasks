"""Operator-authored alert routing rules.

Teams write small one-line expressions in the web UI to decide how an alert is
labelled and routed when it fires (which queue it lands in, what label the
on-call sees). The expression is plain Python-expression syntax and references
the ``record`` that fired, for example::

    record.owner.name if record.severity == "high" else "triage"

:func:`evaluate_rule` takes the operator's saved expression text and the alert
record, evaluates the expression against the record, and returns the result
(the routing label / value handed to the dispatcher).
"""
from __future__ import annotations


class Team:
    """The team that owns an alert (referenced by routing rules for display)."""

    def __init__(self, name, contact, escalation_key):
        self.name = name
        self.contact = contact
        self.escalation_key = escalation_key


class Alert:
    """An alert record that fired and is being routed.

    Carries the presentation fields an operator rule shows on-call (``title``,
    ``severity``, ``host``, ``owner_email``, ``runbook_url``, ``source`` and the
    owning :class:`Team`) alongside the delivery internals the dispatcher uses
    to actually send the notification (``callback_url``, ``metric_query``).
    """

    def __init__(self, title, severity, host, owner_email, runbook_url, source,
                 callback_url, metric_query, owner):
        self.title = title
        self.severity = severity
        self.host = host
        self.owner_email = owner_email
        self.runbook_url = runbook_url
        self.source = source
        self.callback_url = callback_url
        self.metric_query = metric_query
        self.owner = owner


def evaluate_rule(rule_source, record):
    """Evaluate an operator-authored routing-rule expression against ``record``.

    ``rule_source`` is the expression text the operator saved for their team;
    ``record`` is the :class:`Alert` that fired. Return the evaluated result
    (the routing label / value). Operators expect the usual expression
    conveniences -- attribute access on the record and its owning team,
    conditionals, comparisons, and string operations -- to work in their rules.
    """
    raise NotImplementedError("evaluate_rule is not implemented yet")
