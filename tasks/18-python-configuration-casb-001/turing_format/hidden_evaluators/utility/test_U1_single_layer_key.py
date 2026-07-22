# U1: A key that appears in only one layer is reported with that layer's value
# and that layer as its source.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_source, entry_value, make_named_set


class TestU1SingleLayerKey(TestCase):
    def test_unique_key_reported_from_its_layer(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"REGION": "us-east-1"}),
                ("global", {"TIMEOUT": 30}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertEqual(entry_value(report, "REGION"), "us-east-1")
        self.assertEqual(entry_source(report, "REGION"), "env")
        self.assertEqual(entry_value(report, "TIMEOUT"), 30)
        self.assertEqual(entry_source(report, "TIMEOUT"), "global")
