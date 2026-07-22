# U4: Every key that appears anywhere is reported exactly once, and each entry
# carries the documented {"value","source"} shape. (Plain, non-conflicting keys
# only -- this is the "does the report cover everything and have the right
# shape" utility check, not a resolution edge case.)
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_source, entry_value, make_named_set, report_keys


class TestU4CompletenessAndShape(TestCase):
    def test_every_key_once_with_value_and_source(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"A": 1, "B": 2}),
                ("tenant", {"C": 3}),
                ("global", {"D": 4, "E": 5}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertEqual(report_keys(report), {"A", "B", "C", "D", "E"})
        # Each distinct key appears exactly once (dict keys are unique, but also
        # assert the count matches the number of distinct keys across layers).
        self.assertEqual(len(report), 5)

        # Values and sources are correct for these non-conflicting keys.
        self.assertEqual(entry_value(report, "A"), 1)
        self.assertEqual(entry_source(report, "A"), "env")
        self.assertEqual(entry_value(report, "C"), 3)
        self.assertEqual(entry_source(report, "C"), "tenant")
        self.assertEqual(entry_value(report, "E"), 5)
        self.assertEqual(entry_source(report, "E"), "global")
