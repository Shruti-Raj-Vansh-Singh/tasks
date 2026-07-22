# U3: The apply returns an accurate summary and does not disturb bystanders.
#
# The changeset apply returns a JSON-serializable summary that accounts for the
# directives it processed, existing base Enforcer behaviour is unchanged, and a
# subject the changeset never mentions keeps exactly the access it had.
import json
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from casb_helpers import (
    BASE_POLICY,
    make_enforcer,
    grant_role,
    grant_perm,
    revoke_role,
)


class TestU3SummaryAndIsolation(TestCase):
    def test_summary_is_json_serializable_and_counts_directives(self):
        e = make_enforcer(BASE_POLICY)
        changeset = [
            grant_role("carol", "support"),
            grant_perm("dave", "report", "read"),
            revoke_role("bob", "admin"),
        ]
        summary = e.apply_permission_changeset(changeset)
        # must be plain JSON types
        json.dumps(summary)
        self.assertIsInstance(summary, dict)
        # a per-directive account of what happened is present and sized to the batch
        results = summary.get("results")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(changeset))

    def test_bystander_access_unchanged(self):
        # a changeset about carol/dave/bob must not change alice's access.
        e = make_enforcer(BASE_POLICY)
        before = e.enforce("alice", "secret", "read")
        e.apply_permission_changeset(
            [grant_role("carol", "support"), revoke_role("bob", "admin")]
        )
        self.assertEqual(e.enforce("alice", "secret", "read"), before)

    def test_base_enforcer_behaviour_preserved(self):
        # plain enforce() on untouched rules still works.
        e = make_enforcer(BASE_POLICY)
        self.assertTrue(e.enforce("bob", "secret", "read"))
        self.assertFalse(e.enforce("carol", "secret", "read"))
