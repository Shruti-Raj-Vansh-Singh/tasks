# U1: A grant directive in a changeset makes the named access reachable.
#
# After applying a changeset that grants a role or a permission, enforce()
# returns True for the newly granted access.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from casb_helpers import BASE_POLICY, make_enforcer, grant_role, grant_perm


class TestU1GrantsTakeEffect(TestCase):
    def test_grant_role_confers_role_permissions(self):
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("carol", "ticket", "read"))
        e.apply_permission_changeset([grant_role("carol", "support")])
        self.assertTrue(e.enforce("carol", "ticket", "read"))

    def test_grant_permission_confers_direct_access(self):
        e = make_enforcer(BASE_POLICY)
        self.assertFalse(e.enforce("dave", "report", "read"))
        e.apply_permission_changeset([grant_perm("dave", "report", "read")])
        self.assertTrue(e.enforce("dave", "report", "read"))

    def test_multiple_grants_all_take_effect(self):
        e = make_enforcer(BASE_POLICY)
        e.apply_permission_changeset(
            [
                grant_role("carol", "support"),
                grant_perm("dave", "report", "read"),
            ]
        )
        self.assertTrue(e.enforce("carol", "ticket", "read"))
        self.assertTrue(e.enforce("dave", "report", "read"))
