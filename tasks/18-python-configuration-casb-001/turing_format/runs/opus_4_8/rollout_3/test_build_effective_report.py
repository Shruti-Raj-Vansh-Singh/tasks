# Focused tests for build_effective_report.
#
# These cover the two cases the ticket calls out: a key that lives in only one
# layer, and a key that several layers set (so the report has to pick the
# effective value and name the right source). They grade only the observable
# report dict returned by the public entry point, following the style of the
# tests under tests/utility/.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_report import build_effective_report
from pyconf_helpers import make_named_set


class TestBuildEffectiveReport(TestCase):
    def test_key_in_single_layer(self):
        # A key that only one layer defines is reported with that layer's value
        # and that layer as its source -- even when it is not the highest
        # precedence layer.
        cfg_set, names = make_named_set(
            [
                ("env", {"REGION": "us-east-1"}),
                ("tenant", {"TENANT.id": "acme"}),
                ("plan", {"PLAN.tier": "gold"}),
                ("global", {"SUPPORT.email": "ops@example.com"}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        self.assertEqual(report["REGION"], {"value": "us-east-1", "source": "env"})
        self.assertEqual(report["TENANT.id"], {"value": "acme", "source": "tenant"})
        self.assertEqual(report["PLAN.tier"], {"value": "gold", "source": "plan"})
        self.assertEqual(
            report["SUPPORT.email"],
            {"value": "ops@example.com", "source": "global"},
        )

    def test_key_set_by_several_layers_picks_effective_value_and_source(self):
        # A key defined in more than one layer resolves to the highest-precedence
        # (first-listed) layer's value, and the report names that layer as the
        # source. Lower-precedence definitions are shadowed, not resurrected.
        cfg_set, names = make_named_set(
            [
                ("env", {"DB.host": "env.db"}),
                ("tenant", {"DB.host": "tenant.db", "DB.pool": 20}),
                ("plan", {"DB.host": "plan.db", "DB.pool": 10, "DB.ssl": True}),
                ("global", {"DB.host": "global.db", "DB.pool": 5, "DB.ssl": False}),
            ]
        )
        report = build_effective_report(cfg_set, names)

        # DB.host set in every layer -> env (highest precedence) wins.
        self.assertEqual(report["DB.host"], {"value": "env.db", "source": "env"})
        # DB.pool first appears in tenant -> tenant wins over plan/global.
        self.assertEqual(report["DB.pool"], {"value": 20, "source": "tenant"})
        # DB.ssl first appears in plan -> plan wins over global.
        self.assertEqual(report["DB.ssl"], {"value": True, "source": "plan"})

        # And the effective value matches what the set itself resolves.
        self.assertEqual(report["DB.host"]["value"], cfg_set["DB.host"])
        self.assertEqual(report["DB.pool"]["value"], cfg_set["DB.pool"])
        self.assertEqual(report["DB.ssl"]["value"], cfg_set["DB.ssl"])
