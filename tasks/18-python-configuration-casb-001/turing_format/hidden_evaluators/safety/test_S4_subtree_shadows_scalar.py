# S4: When a higher-precedence layer sets a nested subtree under a key and a
# lower layer sets that same key to a scalar, the lower scalar is shadowed and
# must NOT appear in the effective report.
#
# The mirror of S3. Here the higher layer defines FLAGS.beta / FLAGS.gamma (a
# subtree) and the lower layer sets FLAGS to the scalar "all". The effective
# configuration is the subtree; the lower scalar "all" is not in effect. A
# report that keeps both the dotted subtree keys AND the top-level scalar key
# reports a value ("FLAGS" == "all") that the service is not running. Fixing S3
# (drop a lower subtree when a higher scalar exists) does NOT fix S4 (drop a
# lower scalar when a higher subtree exists) -- the shadow runs the other
# direction, so a single one-directional guard leaves this open.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_value, make_named_set, report_keys


class TestS4SubtreeShadowsScalar(TestCase):
    def test_lower_scalar_shadowed_by_higher_subtree(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"FLAGS.beta": True, "FLAGS.gamma": False}),
                ("global", {"FLAGS": "all", "REGION": "eu"}),
            ]
        )
        report = build_effective_report(cfg_set, names)
        keys = report_keys(report)

        # The higher layer's subtree is in effect.
        self.assertEqual(entry_value(report, "FLAGS.beta"), True)
        self.assertEqual(entry_value(report, "FLAGS.gamma"), False)
        # The lower layer's shadowed scalar must NOT be reported.
        self.assertNotIn(
            "FLAGS", keys, "shadowed lower-layer scalar FLAGS leaked into the report"
        )
        # An unrelated lower-layer key is unaffected.
        self.assertEqual(entry_value(report, "REGION"), "eu")
