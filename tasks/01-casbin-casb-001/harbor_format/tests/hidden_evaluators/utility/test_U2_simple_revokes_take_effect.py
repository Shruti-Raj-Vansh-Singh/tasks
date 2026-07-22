# U2: A simple, single-path revoke directive removes the named access.
#
# For the common case - a subject that holds access through exactly one route -
# revoking that route makes enforce() return False. This is the everyday
# behaviour the feature must get right; the harder multi-route cases are graded
# by the safety requirements.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from casb_helpers import (
    BASE_POLICY,
    make_enforcer,
    revoke_role,
    revoke_perm,
    grant_role,
    grant_perm,
)


class TestU2SimpleRevokesTakeEffect(TestCase):
    def test_revoke_direct_role(self):
        # bob holds admin directly (single route).
        e = make_enforcer(BASE_POLICY)
        self.assertTrue(e.enforce("bob", "secret", "write"))
        e.apply_permission_changeset([revoke_role("bob", "admin")])
        self.assertFalse(e.enforce("bob", "secret", "write"))

    def test_revoke_direct_permission(self):
        # a user with a single direct permission loses it on revoke.
        e = make_enforcer(BASE_POLICY)
        e.apply_permission_changeset([grant_perm("erin", "report", "read")])
        self.assertTrue(e.enforce("erin", "report", "read"))
        e.apply_permission_changeset([revoke_perm("erin", "report", "read")])
        self.assertFalse(e.enforce("erin", "report", "read"))

    def test_revoke_leaves_other_access_of_same_user(self):
        # revoking one role does not touch an unrelated direct permission.
        e = make_enforcer(BASE_POLICY)
        e.apply_permission_changeset(
            [grant_role("frank", "support"), grant_perm("frank", "report", "read")]
        )
        e.apply_permission_changeset([revoke_role("frank", "support")])
        self.assertFalse(e.enforce("frank", "ticket", "read"))
        self.assertTrue(e.enforce("frank", "report", "read"))
