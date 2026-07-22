# Focused tests for PolicyAdminEnforcer.apply_permission_changeset.
#
# These tests grade OBSERVABLE behaviour only: they build a PolicyAdminEnforcer
# on a real RBAC model, drive it through the public apply_permission_changeset
# entry point, and then ask enforce() what access a subject ends up with. They
# follow the style and fixtures of the tests under tests/utility/.
import json
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from casb_helpers import (
    BASE_POLICY,
    make_enforcer,
    grant_role,
    grant_perm,
    revoke_role,
    revoke_perm,
    revoke_results,
    reported_removed,
)


class TestApplyPermissionChangeset(TestCase):
    # --- grants -----------------------------------------------------------

    def test_grant_role_confers_access(self):
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("carol", "ticket", "read"))
        summary = e.apply_permission_changeset([grant_role("carol", "support")])
        self.assertTrue(e.enforce("carol", "ticket", "read"))
        self.assertEqual(summary["granted"], 1)
        self.assertEqual(summary["revoked"], 0)

    def test_grant_permission_confers_direct_access(self):
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("dave", "report", "read"))
        summary = e.apply_permission_changeset([grant_perm("dave", "report", "read")])
        self.assertTrue(e.enforce("dave", "report", "read"))
        self.assertEqual(summary["granted"], 1)

    # --- simple revokes ---------------------------------------------------

    def test_revoke_role_removes_access(self):
        # bob holds admin directly (single route).
        e = make_enforcer(BASE_POLICY)
        self.assertTrue(e.enforce("bob", "secret", "write"))
        summary = e.apply_permission_changeset([revoke_role("bob", "admin")])
        self.assertFalse(e.enforce("bob", "secret", "write"))
        self.assertEqual(summary["revoked"], 1)

    def test_revoke_permission_removes_access(self):
        # a user with a single direct permission loses it on revoke.
        e = make_enforcer(BASE_POLICY)
        e.apply_permission_changeset([grant_perm("erin", "report", "read")])
        self.assertTrue(e.enforce("erin", "report", "read"))
        e.apply_permission_changeset([revoke_perm("erin", "report", "read")])
        self.assertFalse(e.enforce("erin", "report", "read"))

    # --- summary lines up with what actually happened ---------------------

    def test_summary_is_json_serializable_and_sized_to_batch(self):
        e = make_enforcer(BASE_POLICY)
        changeset = [
            grant_role("carol", "support"),
            grant_perm("dave", "report", "read"),
            revoke_role("bob", "admin"),
        ]
        summary = e.apply_permission_changeset(changeset)
        json.dumps(summary)  # must be plain JSON types
        self.assertIsInstance(summary, dict)
        self.assertIn("applied", summary)
        self.assertEqual(summary["granted"], 2)
        self.assertEqual(summary["revoked"], 1)
        results = summary["results"]
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(changeset))

    def test_grant_summary_matches_enforce(self):
        e = make_enforcer(BASE_POLICY)
        summary = e.apply_permission_changeset(
            [grant_role("carol", "support"), grant_perm("dave", "report", "read")]
        )
        for r in summary["results"]:
            self.assertTrue(r.get("ok"))
        self.assertTrue(e.enforce("carol", "ticket", "read"))
        self.assertTrue(e.enforce("dave", "report", "read"))

    def test_revoke_report_true_only_when_access_actually_gone(self):
        # For the simple single-route case the revoke report claims removal,
        # and enforce() agrees the access is gone.
        e = make_enforcer(BASE_POLICY)
        summary = e.apply_permission_changeset([revoke_role("bob", "admin")])
        for r in revoke_results(summary):
            claimed_removed = reported_removed(r)
            still_has = e.enforce("bob", "secret", "write")
            # the report must not claim removal while access remains
            if claimed_removed:
                self.assertFalse(still_has)

    def test_revoke_report_never_lies_when_access_survives_via_role(self):
        # alice reaches secret through a role chain (alice -> manager -> admin).
        # Revoking the direct permission rule for the shared `admin` route is
        # not part of this directive; a revoke that names alice's access must
        # not claim removal while alice can still exercise it.
        policy = BASE_POLICY + "p, alice, secret, read\n"
        e = make_enforcer(policy)
        self.assertTrue(e.enforce("alice", "secret", "read"))
        summary = e.apply_permission_changeset([revoke_perm("alice", "secret", "read")])
        still_has = e.enforce("alice", "secret", "read")
        # alice still reaches secret,read via manager -> admin, so it survives.
        self.assertTrue(still_has)
        for r in revoke_results(summary):
            # report must be truthful: it may not say "removed" while alice can
            # still exercise the access.
            if reported_removed(r):
                self.assertFalse(still_has)

    # --- isolation --------------------------------------------------------

    def test_bystander_access_unchanged(self):
        e = make_enforcer(BASE_POLICY)
        before = e.enforce("alice", "secret", "read")
        e.apply_permission_changeset(
            [grant_role("carol", "support"), revoke_role("bob", "admin")]
        )
        self.assertEqual(e.enforce("alice", "secret", "read"), before)
