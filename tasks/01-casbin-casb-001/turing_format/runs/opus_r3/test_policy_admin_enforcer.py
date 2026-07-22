# Focused tests for PolicyAdminEnforcer.apply_permission_changeset.
#
# These tests grade OBSERVABLE behaviour only: they build a PolicyAdminEnforcer
# on a real RBAC model, apply a changeset through the public
# apply_permission_changeset(...) entry point, then ask enforce(...) what access
# a subject ends up with and read the returned summary. They mirror the fixtures
# and style of the tests under tests/utility/ and reuse tests/casb_helpers.py.
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


class TestPolicyAdminEnforcer(TestCase):
    # -- grants ---------------------------------------------------------------

    def test_grant_role_takes_effect(self):
        # carol has no access to the support role's resource until granted it.
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("carol", "ticket", "read"))

        summary = e.apply_permission_changeset([grant_role("carol", "support")])

        self.assertTrue(e.enforce("carol", "ticket", "read"))
        self.assertEqual(summary["granted"], 1)
        self.assertEqual(summary["applied"], 1)

    def test_grant_permission_takes_effect(self):
        # dave gets a direct permission he did not have before.
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("dave", "report", "read"))

        summary = e.apply_permission_changeset([grant_perm("dave", "report", "read")])

        self.assertTrue(e.enforce("dave", "report", "read"))
        self.assertEqual(summary["granted"], 1)

    # -- revokes (straightforward, single-route) ------------------------------

    def test_revoke_role_takes_effect(self):
        # bob holds admin by a single direct route; revoking it removes access.
        e = make_enforcer(BASE_POLICY)
        self.assertTrue(e.enforce("bob", "secret", "write"))

        summary = e.apply_permission_changeset([revoke_role("bob", "admin")])

        self.assertFalse(e.enforce("bob", "secret", "write"))
        self.assertEqual(summary["revoked"], 1)

    def test_revoke_permission_takes_effect(self):
        # a subject with a single direct permission loses it on revoke.
        e = make_enforcer(BASE_POLICY)
        e.apply_permission_changeset([grant_perm("erin", "report", "read")])
        self.assertTrue(e.enforce("erin", "report", "read"))

        summary = e.apply_permission_changeset([revoke_perm("erin", "report", "read")])

        self.assertFalse(e.enforce("erin", "report", "read"))
        self.assertEqual(summary["revoked"], 1)

    # -- the summary lines up with what actually happened ---------------------

    def test_summary_is_json_serializable_and_per_directive(self):
        e = make_enforcer(BASE_POLICY)
        changeset = [
            grant_role("carol", "support"),
            grant_perm("dave", "report", "read"),
            revoke_role("bob", "admin"),
        ]

        summary = e.apply_permission_changeset(changeset)

        # summary is a plain JSON-serializable dict with the documented keys.
        json.dumps(summary)
        self.assertIsInstance(summary, dict)
        for key in ("applied", "granted", "revoked", "results"):
            self.assertIn(key, summary)

        results = summary["results"]
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(changeset))
        # counts add up: 2 grants and 1 revoke, all effective on this changeset.
        self.assertEqual(summary["granted"], 2)
        self.assertEqual(summary["revoked"], 1)

    def test_revoke_report_matches_actual_access(self):
        # The report about a revoke must agree with what enforce() says
        # afterwards: it may claim the access was removed only when the subject
        # genuinely no longer has it.
        e = make_enforcer(BASE_POLICY)
        changeset = [
            revoke_role("bob", "admin"),
            grant_perm("erin", "report", "read"),
            revoke_perm("erin", "report", "read"),
        ]

        summary = e.apply_permission_changeset(changeset)

        # bob no longer reaches admin's permissions; erin's direct perm is gone.
        self.assertFalse(e.enforce("bob", "secret", "read"))
        self.assertFalse(e.enforce("erin", "report", "read"))

        for entry in revoke_results(summary):
            self.assertTrue(reported_removed(entry))

    def test_bystander_access_is_untouched(self):
        # A changeset about carol/dave/bob must not change alice's access.
        e = make_enforcer(BASE_POLICY)
        before = e.enforce("alice", "secret", "read")

        e.apply_permission_changeset(
            [grant_role("carol", "support"), revoke_role("bob", "admin")]
        )

        self.assertEqual(e.enforce("alice", "secret", "read"), before)
