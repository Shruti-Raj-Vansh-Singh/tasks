# Focused tests for build_effective_report, following the style of the
# fixtures under tests/utility/. These grade only the observable report dict.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_source, entry_value, make_named_set, report_keys


class TestBuildEffectiveReport(TestCase):
    def test_key_in_only_one_layer(self):
        # A key that lives in exactly one layer is reported with that layer's
        # value and that layer named as its source.
        cfg_set, names = make_named_set(
            [
                ("env", {"REGION": "us-west-2"}),
                ("tenant", {"TENANT.id": "acme"}),
                ("plan", {"PLAN.tier": "gold"}),
                ("global", {"BASELINE.timeout": 30}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # Each unique key resolves to its sole layer.
        self.assertEqual(entry_value(report, "REGION"), "us-west-2")
        self.assertEqual(entry_source(report, "REGION"), "env")

        self.assertEqual(entry_value(report, "TENANT.id"), "acme")
        self.assertEqual(entry_source(report, "TENANT.id"), "tenant")

        self.assertEqual(entry_value(report, "PLAN.tier"), "gold")
        self.assertEqual(entry_source(report, "PLAN.tier"), "plan")

        self.assertEqual(entry_value(report, "BASELINE.timeout"), 30)
        self.assertEqual(entry_source(report, "BASELINE.timeout"), "global")

        # Completeness + shape: every key once, documented dict shape.
        self.assertEqual(
            report_keys(report),
            {"REGION", "TENANT.id", "PLAN.tier", "BASELINE.timeout"},
        )
        for entry in report.values():
            self.assertIsInstance(entry, dict)
            self.assertEqual(set(entry.keys()), {"value", "source"})

    def test_key_set_by_several_layers_picks_effective_value_and_source(self):
        # A key defined in several layers must report the effective value (the
        # highest-precedence one) and name the layer that actually supplied it,
        # not a shadowed lower-precedence layer.
        cfg_set, names = make_named_set(
            [
                ("env", {"DB.pool": 50}),
                ("tenant", {"DB.pool": 30, "DB.host": "tenant.db.internal"}),
                ("plan", {"DB.pool": 20, "DB.host": "plan.db.internal"}),
                ("global", {"DB.pool": 5, "DB.host": "global.db.internal"}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # DB.pool is set in all four layers; env (highest precedence) wins.
        self.assertEqual(entry_value(report, "DB.pool"), 50)
        self.assertEqual(entry_source(report, "DB.pool"), "env")

        # DB.host is set in tenant/plan/global (not env); tenant wins because it
        # is the highest-precedence layer that defines it.
        self.assertEqual(entry_value(report, "DB.host"), "tenant.db.internal")
        self.assertEqual(entry_source(report, "DB.host"), "tenant")

        # Only the two distinct keys are reported, each once.
        self.assertEqual(report_keys(report), {"DB.pool", "DB.host"})
        self.assertEqual(len(report), 2)
