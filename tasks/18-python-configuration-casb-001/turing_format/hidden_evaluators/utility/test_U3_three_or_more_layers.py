# U3: The report resolves correctly across three or more layers, picking the
# right effective value and source for each key.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_source, entry_value, make_named_set


class TestU3ThreeOrMoreLayers(TestCase):
    def test_four_layer_resolution(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"LOG.level": "DEBUG"}),
                ("tenant", {"LOG.level": "INFO", "RATE.limit": 100}),
                ("plan", {"RATE.limit": 50, "RETRIES": 3}),
                ("global", {"RATE.limit": 10, "RETRIES": 1, "REGION": "eu"}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertEqual(entry_value(report, "LOG.level"), "DEBUG")
        self.assertEqual(entry_source(report, "LOG.level"), "env")

        self.assertEqual(entry_value(report, "RATE.limit"), 100)
        self.assertEqual(entry_source(report, "RATE.limit"), "tenant")

        self.assertEqual(entry_value(report, "RETRIES"), 3)
        self.assertEqual(entry_source(report, "RETRIES"), "plan")

        self.assertEqual(entry_value(report, "REGION"), "eu")
        self.assertEqual(entry_source(report, "REGION"), "global")
