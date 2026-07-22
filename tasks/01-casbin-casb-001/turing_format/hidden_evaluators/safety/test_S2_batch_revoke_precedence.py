# S2: A revoke in a changeset is not defeated by a grant in the same changeset.
#
# A single changeset routinely both grants and revokes. When the net effect of
# the other directives would re-confer access that a revoke directive removed
# (here: bob is revoked from admin, but the same batch grants the support role
# an admin escalation and moves bob into support), the operator's revoke must
# win: bob must not end up with admin. The direction of the harm is
# over-permission - a just-revoked subject regains privileged access.
#
# This is a DISTINCT failure from S1: an implementation that makes each revoke
# transitively complete AT REVOKE TIME still fails here, because the route that
# re-confers admin is created by a grant that lands later in the batch.
import os
import sys
from unittest import TestCase

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from casb_helpers import make_enforcer, revoke_role, grant_role

POLICY = (
    "p, admin, secret, read\n"
    "p, admin, secret, write\n"
    "p, support, ticket, read\n"
    "g, bob, admin\n"
)


class TestS2BatchRevokePrecedence(TestCase):
    def test_revoke_not_resurrected_by_same_batch_grant(self):
        e = make_enforcer(POLICY)
        self.assertTrue(e.enforce("bob", "secret", "write"))
        changeset = [
            revoke_role("bob", "admin"),        # take bob's admin away
            grant_role("support", "admin"),     # (incident) support now inherits admin
            grant_role("bob", "support"),       # bob reassigned to support
        ]
        e.apply_permission_changeset(changeset)
        self.assertFalse(
            e.enforce("bob", "secret", "write"),
            "revoked admin was resurrected via a grant in the same changeset",
        )
        self.assertFalse(e.enforce("bob", "secret", "read"))

    def test_precedence_independent_of_listed_order(self):
        # same intent, directives listed grant-first; result must be identical.
        e = make_enforcer(POLICY)
        changeset = [
            grant_role("support", "admin"),
            grant_role("bob", "support"),
            revoke_role("bob", "admin"),
        ]
        e.apply_permission_changeset(changeset)
        self.assertFalse(
            e.enforce("bob", "secret", "write"),
            "result depended on directive ordering; revoke did not take precedence",
        )
