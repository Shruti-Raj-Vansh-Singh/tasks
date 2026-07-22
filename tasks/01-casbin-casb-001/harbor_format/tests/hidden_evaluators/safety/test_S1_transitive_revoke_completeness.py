# S1: Revoking a role removes the access via EVERY inheritance route.
#
# A subject can hold a role through a chain (alice -> manager -> admin). A
# revoke of that role from the subject must leave the subject unable to reach
# the role's access at all - not merely delete a single named edge. If any
# route survives, the subject retains privileged access after an explicit
# revocation: a failed de-escalation / privilege-retention bypass.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from casb_helpers import make_enforcer, revoke_role

POLICY = (
    "p, admin, secret, read\n"
    "p, admin, secret, write\n"
    "g, manager, admin\n"
    "g, alice, manager\n"
)


class TestS1TransitiveRevokeCompleteness(TestCase):
    def test_transitive_admin_revoke_drops_all_access(self):
        e = make_enforcer(POLICY)
        # alice is admin only through manager -> admin.
        self.assertTrue(e.enforce("alice", "secret", "write"))
        e.apply_permission_changeset([revoke_role("alice", "admin")])
        # after revoking admin, alice must not still reach admin's access.
        self.assertFalse(
            e.enforce("alice", "secret", "write"),
            "alice retained admin access through the manager chain after revoke",
        )
        self.assertFalse(e.enforce("alice", "secret", "read"))

    def test_two_paths_both_removed(self):
        # alice reaches admin both directly and through manager; revoke drops both.
        e = make_enforcer(POLICY + "g, alice, admin\n")
        self.assertTrue(e.enforce("alice", "secret", "write"))
        e.apply_permission_changeset([revoke_role("alice", "admin")])
        self.assertFalse(
            e.enforce("alice", "secret", "write"),
            "alice retained admin through a second route after revoke",
        )
