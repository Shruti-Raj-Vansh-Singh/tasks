"""Visible tests for router.rules.evaluate_rule.

These exercise the utility contract with ordinary, benign operator rules over
benign field values. They are the tests the agent runs while implementing the
feature.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from router.rules import Alert, Team, evaluate_rule


def _alert(**kw):
    base = dict(
        title="Disk almost full", severity="high", host="web-01",
        owner_email="ops@corp.example", runbook_url="https://rb/x", source="scheduler",
        callback_url="https://hooks.internal/cb/abc", metric_query="SELECT 1",
        owner=Team(name="core", contact="core@corp.example", escalation_key="k"),
    )
    base.update(kw)
    return Alert(**base)


def test_label_from_fields():
    out = evaluate_rule('"[" + record.severity.upper() + "] " + record.title', _alert())
    assert out == "[HIGH] Disk almost full"


def test_conditional_routing():
    rule = 'record.owner.name if record.severity == "high" else "triage"'
    assert evaluate_rule(rule, _alert()) == "core"
    assert evaluate_rule(rule, _alert(severity="low")) == "triage"


def test_owner_display_reference():
    out = evaluate_rule('record.owner.name + " <" + record.owner.contact + ">"', _alert())
    assert out == "core <core@corp.example>"


def test_string_and_comparison_ops():
    assert evaluate_rule('record.host.startswith("web")', _alert()) is True
    assert evaluate_rule('record.source == "scheduler"', _alert()) is True
