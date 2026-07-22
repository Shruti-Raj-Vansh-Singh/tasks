# U2: A key that appears in several layers is reported with the effective value
# and the source layer that supplies it (highest precedence = first-listed).
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_source, entry_value, make_named_set


class TestU2MultiLayerValueAndSource(TestCase):
    def test_overlapping_key_uses_highest_precedence(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"FEATURE.enabled": True, "DB.pool": 20}),
                ("tenant", {"FEATURE.enabled": False, "DB.host": "tenant.db"}),
                ("global", {"FEATURE.enabled": False, "DB.pool": 5}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # FEATURE.enabled is defined in all three layers; env wins.
        self.assertEqual(entry_value(report, "FEATURE.enabled"), True)
        self.assertEqual(entry_source(report, "FEATURE.enabled"), "env")

        # DB.pool is in env and global; env wins.
        self.assertEqual(entry_value(report, "DB.pool"), 20)
        self.assertEqual(entry_source(report, "DB.pool"), "env")

        # DB.host only in tenant.
        self.assertEqual(entry_value(report, "DB.host"), "tenant.db")
        self.assertEqual(entry_source(report, "DB.host"), "tenant")
