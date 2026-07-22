# S3: When a higher-precedence layer sets a key to a scalar and a lower layer
# has a nested subtree under that same key, the lower subtree is shadowed and
# must NOT appear in the effective report.
#
# The effective value of CACHE is the higher layer's scalar ("disabled"); the
# lower layer's CACHE.ttl / CACHE.size are not in effect at all. Because the
# library stores nested config as flattened dotted keys, a scalar "CACHE" and a
# subtree "CACHE.ttl"/"CACHE.size" do not collide as dict keys, so a report that
# merges keys without honoring the scalar-over-subtree shadow will resurrect the
# lower layer's disabled-away settings -- reporting a configuration the service
# is not actually running (a stale / over-broad effective view). This is
# orthogonal to the masking seams (S1/S2): it is about which keys are in effect,
# not about redacting values.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config_report import build_effective_report
from pyconf_helpers import entry_value, make_named_set, report_keys


class TestS3ScalarShadowsSubtree(TestCase):
    def test_lower_subtree_shadowed_by_higher_scalar(self):
        cfg_set, names = make_named_set(
            [
                ("env", {"CACHE": "disabled"}),
                ("global", {"CACHE.ttl": 300, "CACHE.size": 10, "REGION": "eu"}),
            ]
        )
        report = build_effective_report(cfg_set, names)
        keys = report_keys(report)

        # The higher layer's scalar is in effect.
        self.assertEqual(entry_value(report, "CACHE"), "disabled")
        # The lower layer's shadowed subtree must NOT be reported.
        self.assertNotIn(
            "CACHE.ttl", keys, "shadowed lower-layer CACHE.ttl leaked into the report"
        )
        self.assertNotIn(
            "CACHE.size", keys, "shadowed lower-layer CACHE.size leaked into the report"
        )
        # An unrelated lower-layer key is unaffected.
        self.assertEqual(entry_value(report, "REGION"), "eu")
