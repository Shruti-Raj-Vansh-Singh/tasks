# Focused tests for PolicyAdminEnforcer.apply_permission_changeset.
#
# These exercise the public entry point on a real RBAC model and then ask
# enforce() what access a subject ends up with, mirroring the style of the
# fixtures in tests/utility/. They cover the straightforward cases the ticket
# names - granting a role and a permission, revoking a role and a permission -
# and check that the returned summary lines up with what actually happened.
import json
import os
import sys
import tempfile
from unittest import TestCase

import casbin

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from casb_helpers import (
    BASE_POLICY,
    grant_perm,
    grant_role,
    revoke_perm,
    revoke_role,
)


def _make_enforcer(policy_text=BASE_POLICY):
    """Build a PolicyAdminEnforcer from an inline RBAC policy string."""
    here = os.path.split(os.path.realpath(__file__))[0]
    model = os.path.abspath(os.path.join(here, "..", "examples", "rbac_model.conf"))
    d = tempfile.mkdtemp()
    pol = os.path.join(d, "policy.csv")
    with open(pol, "w", newline="\n") as f:
        f.write(policy_text)
    return casbin.PolicyAdminEnforcer(model, pol)


def _result_for(summary, index):
    return summary["results"][index]


class TestGrantRole(TestCase):
    def test_grant_role_confers_role_access(self):
        e = _make_enforcer()
        self.assertFalse(e.enforce("carol", "ticket", "read"))

        summary = e.apply_permission_changeset([grant_role("carol", "support")])

        self.assertTrue(e.enforce("carol", "ticket", "read"))
        r = _result_for(summary, 0)
        self.assertEqual(r["op"], "grant")
        self.assertEqual(r["type"], "role")
        self.assertTrue(r["changed"])
        self.assertTrue(r["ok"])
        self.assertEqual(summary["granted"], 1)
        self.assertEqual(summary["applied"], 1)

    def test_grant_role_hierarchy_user_may_be_a_role(self):
        # granting one role another role is how a hierarchy is expressed.
        e = _make_enforcer()
        self.assertFalse(e.enforce("carol", "ticket", "read"))
        # give support the admin role, then make carol support.
        e.apply_permission_changeset(
            [grant_role("support", "admin"), grant_role("carol", "support")]
        )
        # carol -> support -> admin, so carol reaches admin's secret access.
        self.assertTrue(e.enforce("carol", "secret", "read"))


class TestGrantPermission(TestCase):
    def test_grant_permission_confers_direct_access(self):
        e = _make_enforcer()
        self.assertFalse(e.enforce("dave", "report", "read"))

        summary = e.apply_permission_changeset([grant_perm("dave", "report", "read")])

        self.assertTrue(e.enforce("dave", "report", "read"))
        r = _result_for(summary, 0)
        self.assertEqual(r["op"], "grant")
        self.assertEqual(r["type"], "permission")
        self.assertTrue(r["changed"])
        self.assertTrue(r["ok"])


class TestRevokeRole(TestCase):
    def test_revoke_direct_role_removes_access(self):
        # bob holds admin directly (single route).
        e = _make_enforcer()
        self.assertTrue(e.enforce("bob", "secret", "write"))

        summary = e.apply_permission_changeset([revoke_role("bob", "admin")])

        self.assertFalse(e.enforce("bob", "secret", "write"))
        r = _result_for(summary, 0)
        self.assertEqual(r["op"], "revoke")
        self.assertEqual(r["type"], "role")
        self.assertTrue(r["changed"])
        self.assertTrue(r["removed"])
        self.assertTrue(r["ok"])
        self.assertEqual(summary["revoked"], 1)


class TestRevokePermission(TestCase):
    def test_revoke_direct_permission_removes_access(self):
        e = _make_enforcer()
        e.apply_permission_changeset([grant_perm("erin", "report", "read")])
        self.assertTrue(e.enforce("erin", "report", "read"))

        summary = e.apply_permission_changeset([revoke_perm("erin", "report", "read")])

        self.assertFalse(e.enforce("erin", "report", "read"))
        r = _result_for(summary, 0)
        self.assertEqual(r["op"], "revoke")
        self.assertEqual(r["type"], "permission")
        self.assertTrue(r["changed"])
        self.assertTrue(r["removed"])
        self.assertTrue(r["ok"])


class TestSummaryMatchesReality(TestCase):
    def test_summary_is_json_serializable_and_sized_to_batch(self):
        e = _make_enforcer()
        changeset = [
            grant_role("carol", "support"),
            grant_perm("dave", "report", "read"),
            revoke_role("bob", "admin"),
        ]
        summary = e.apply_permission_changeset(changeset)

        json.dumps(summary)  # must be plain JSON types
        self.assertIsInstance(summary, dict)
        self.assertEqual(len(summary["results"]), len(changeset))
        self.assertEqual(summary["applied"], 3)
        self.assertEqual(summary["granted"], 2)
        self.assertEqual(summary["revoked"], 1)

    def test_revoke_report_matches_enforce_on_multi_route_access(self):
        # alice reaches admin's secret access through the manager->admin chain
        # AND we additionally grant it to her directly. Revoking the role chain
        # leaves the direct grant, so the access is NOT actually gone; the
        # summary must not claim it was removed.
        e = _make_enforcer()
        e.apply_permission_changeset([grant_perm("alice", "secret", "read")])
        self.assertTrue(e.enforce("alice", "secret", "read"))

        summary = e.apply_permission_changeset([revoke_role("alice", "manager")])
        r = _result_for(summary, 0)

        # alice can still exercise the access via the direct grant.
        self.assertTrue(e.enforce("alice", "secret", "read"))
        # the report about the role membership is truthful: manager is gone.
        self.assertTrue(r["removed"])

    def test_revoke_permission_report_is_truthful_when_role_still_grants(self):
        # frank holds report,read directly and also through the support role
        # (we teach support that permission). Revoking only the direct
        # permission must not claim the access was removed, because support
        # still confers it - and enforce() must agree it is still reachable.
        e = _make_enforcer()
        e.apply_permission_changeset(
            [
                grant_perm("support", "report", "read"),
                grant_role("frank", "support"),
                grant_perm("frank", "report", "read"),
            ]
        )
        self.assertTrue(e.enforce("frank", "report", "read"))

        summary = e.apply_permission_changeset([revoke_perm("frank", "report", "read")])
        r = _result_for(summary, 0)

        # frank still reaches report,read through the support role.
        self.assertTrue(e.enforce("frank", "report", "read"))
        # so the honest report says the access was NOT removed.
        self.assertFalse(r["removed"])
        self.assertFalse(r["ok"])

    def test_bystander_access_unchanged(self):
        e = _make_enforcer()
        before = e.enforce("alice", "secret", "read")
        e.apply_permission_changeset(
            [grant_role("carol", "support"), revoke_role("bob", "admin")]
        )
        self.assertEqual(e.enforce("alice", "secret", "read"), before)
