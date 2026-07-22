# Focused tests for build_effective_report, following the style of the
# existing tests under tests/utility/ and reusing the shared fixtures in
# pyconf_helpers. These grade only the observable report dict returned by the
# public entry point.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_report import build_effective_report  # noqa: E402
from pyconf_helpers import (  # noqa: E402
    entry_source,
    entry_value,
    make_named_set,
    report_keys,
)


class TestBuildEffectiveReport(TestCase):
    def test_key_in_only_one_layer(self):
        # A key present in a single layer is reported with that layer's value
        # and named as sourced from that layer.
        cfg_set, names = make_named_set(
            [
                ("env", {"REGION": "us-west-2"}),
                ("tenant", {"DB.host": "tenant.db.internal"}),
                ("global", {"TIMEOUT": 30}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # DB.host lives only in the tenant layer.
        self.assertEqual(entry_value(report, "DB.host"), "tenant.db.internal")
        self.assertEqual(entry_source(report, "DB.host"), "tenant")

        # TIMEOUT lives only in the global layer.
        self.assertEqual(entry_value(report, "TIMEOUT"), 30)
        self.assertEqual(entry_source(report, "TIMEOUT"), "global")

    def test_key_set_by_several_layers_uses_effective_value_and_source(self):
        # A key set in several layers must report the effective (highest
        # precedence) value and name the layer that actually supplied it.
        cfg_set, names = make_named_set(
            [
                ("env", {"LOG.level": "DEBUG"}),
                ("tenant", {"LOG.level": "INFO", "RATE.limit": 100}),
                ("plan", {"LOG.level": "WARN", "RATE.limit": 50}),
                ("global", {"LOG.level": "ERROR", "RATE.limit": 10}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # LOG.level is set by all four layers; env (highest precedence) wins.
        self.assertEqual(entry_value(report, "LOG.level"), "DEBUG")
        self.assertEqual(entry_source(report, "LOG.level"), "env")

        # RATE.limit is set by tenant, plan and global; tenant wins (env does
        # not set it), so neither the plan nor global values should appear.
        self.assertEqual(entry_value(report, "RATE.limit"), 100)
        self.assertEqual(entry_source(report, "RATE.limit"), "tenant")

        # Both keys are reported exactly once and nothing else leaks in.
        self.assertEqual(report_keys(report), {"LOG.level", "RATE.limit"})
        self.assertEqual(len(report), 2)
