# Copyright 2021 The casbin Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from casbin.enforcer import Enforcer


class PolicyAdminEnforcer(Enforcer):
    """Enforcer that can apply a batch of permission changes in one call.

    Services that mirror access rules from an upstream system of record (an
    HR directory, an IAM export, a ticketing workflow) receive their updates
    as a *changeset*: a list of grant and revoke directives to bring the
    running policy in line with the source. Rather than making the caller
    loop over the per-edit management API and reason about ordering,
    ``PolicyAdminEnforcer`` exposes a single :meth:`apply_permission_changeset`
    entry point that takes the whole changeset and returns a summary of what
    it did.

    A directive is a plain dict. Each has an ``"op"`` of ``"grant"`` or
    ``"revoke"`` and a ``"type"`` of ``"role"`` or ``"permission"``:

    * role directive::

          {"op": "grant",  "type": "role", "user": "alice", "role": "admin"}
          {"op": "revoke", "type": "role", "user": "alice", "role": "admin"}

      (``"user"`` may itself be a role name, e.g. granting ``support`` the
      ``admin`` role, which is how casbin expresses a role hierarchy.)

    * permission directive::

          {"op": "grant",  "type": "permission",
           "user": "alice", "perm": ["data1", "read"]}
          {"op": "revoke", "type": "permission",
           "user": "alice", "perm": ["data1", "read"]}

    ``apply_permission_changeset(changeset)`` applies every directive to the
    underlying policy and returns a JSON-serializable summary dict. The
    intended summary keys are:

    * ``"applied"`` - number of directives that changed the policy,
    * ``"granted"`` / ``"revoked"`` - per-op counts,
    * ``"results"`` - a per-directive list describing the outcome of each.

    The exact shape of ``"results"`` entries is up to the implementation, but
    a caller should be able to read the summary and know, for each revoke
    directive, whether the access it named was actually removed.

    See ``docs/policy_administration.md`` for the guarantees a changeset apply
    is expected to uphold.
    """

    def apply_permission_changeset(self, changeset):
        """Apply a changeset of grant/revoke directives and return a summary.

        Each directive is applied in order. The returned summary is a plain
        (JSON-serializable) dict with:

        * ``"applied"``  - number of directives that actually changed the policy,
        * ``"granted"``  - number of grant directives that changed the policy,
        * ``"revoked"``  - number of revoke directives that removed the access,
        * ``"results"``  - one entry per directive, in order.

        Each ``results`` entry echoes the directive's ``op`` and ``type`` and
        records the outcome. For a revoke, ``"removed"`` reports whether the
        subject genuinely no longer has the named access *after* the apply -
        established by re-checking the running policy, not by trusting that a
        single rule was deleted. A revoke is only ever reported with
        ``"removed": True`` when the subject truly can no longer reach the
        access; anything else would tell the operator something untrue.
        """
        results = []
        granted = 0
        revoked = 0
        applied = 0

        for directive in changeset:
            result = self._apply_directive(directive)
            results.append(result)

            if result.get("changed"):
                applied += 1

            op = result.get("op")
            if op == "grant" and result.get("changed"):
                granted += 1
            elif op == "revoke" and result.get("removed"):
                revoked += 1

        return {
            "applied": applied,
            "granted": granted,
            "revoked": revoked,
            "results": results,
        }

    def _apply_directive(self, directive):
        op = directive.get("op")
        dtype = directive.get("type")

        if op == "grant" and dtype == "role":
            return self._grant_role(directive)
        if op == "grant" and dtype == "permission":
            return self._grant_permission(directive)
        if op == "revoke" and dtype == "role":
            return self._revoke_role(directive)
        if op == "revoke" and dtype == "permission":
            return self._revoke_permission(directive)

        raise ValueError("unknown changeset directive: op={!r} type={!r}".format(op, dtype))

    # ------------------------------------------------------------------ grants

    def _grant_role(self, directive):
        user = directive["user"]
        role = directive["role"]

        # add_role_for_user is idempotent: it returns False if the edge already
        # existed. Either way, once we return the subject reaches the role.
        changed = self.add_role_for_user(user, role)

        return {
            "op": "grant",
            "type": "role",
            "user": user,
            "role": role,
            "changed": bool(changed),
            "granted": self._has_role(user, role),
        }

    def _grant_permission(self, directive):
        user = directive["user"]
        perm = list(directive["perm"])

        changed = self.add_permission_for_user(user, *perm)

        return {
            "op": "grant",
            "type": "permission",
            "user": user,
            "perm": perm,
            "changed": bool(changed),
            "granted": self.enforce(user, *perm),
        }

    # --------------------------------------------------------------- revocations

    def _revoke_role(self, directive):
        """Revoke a role from a subject.

        The named access is "the subject holds role ``role``". Removing the one
        ``g, user, role`` edge is not enough: the subject may reach ``role``
        through a chain of intermediate roles it holds. We therefore sever
        every one of the *subject's own* grouping edges that leads to ``role``,
        which takes the role away from the subject without disturbing any other
        subject (only edges originating at ``user`` are touched). Edges to
        roles that do not lead to ``role`` are left in place, so the subject's
        unrelated access is preserved.
        """
        user = directive["user"]
        role = directive["role"]

        changed = self._sever_routes_to(user, lambda target: target == role or self._reaches(target, role))

        removed = not self._has_role(user, role)

        return {
            "op": "revoke",
            "type": "role",
            "user": user,
            "role": role,
            "changed": bool(changed),
            "removed": bool(removed),
        }

    def _revoke_permission(self, directive):
        """Revoke a permission from a subject.

        The named access is "``enforce(user, *perm)`` is True". A permission can
        be held directly (``p, user, obj, act``) and/or through one or more
        roles the subject holds. We first drop the subject's direct rule, then,
        if the subject can still reach the permission, sever the subject's own
        routes to any role that grants it. As with role revokes we only ever
        remove edges/rules belonging to the named subject, so bystanders that
        share those roles keep their access. ``removed`` is decided by asking
        ``enforce`` afterwards, so it is only True when the subject genuinely
        can no longer exercise the permission.
        """
        user = directive["user"]
        perm = list(directive["perm"])

        changed = self.delete_permission_for_user(user, *perm)
        changed = bool(changed)

        # If the subject can still reach the permission, it is coming through a
        # role. Sever the subject's own routes to the roles that grant it.
        if self.enforce(user, *perm):
            granting_roles = [
                r for r in self.get_implicit_roles_for_user(user) if self.has_permission_for_user(r, *perm)
            ]
            if granting_roles:
                severed = self._sever_routes_to(
                    user,
                    lambda target: any(target == g or self._reaches(target, g) for g in granting_roles),
                )
                changed = changed or severed

        removed = not self.enforce(user, *perm)

        return {
            "op": "revoke",
            "type": "permission",
            "user": user,
            "perm": perm,
            "changed": changed,
            "removed": bool(removed),
        }

    # ------------------------------------------------------------------ helpers

    def _has_role(self, user, role):
        """Whether the subject reaches ``role`` by any route (direct or chained)."""
        if user == role:
            return True
        return role in self.get_implicit_roles_for_user(user)

    def _reaches(self, source, target):
        """Whether role/user ``source`` reaches ``target`` through the role graph."""
        if source == target:
            return True
        return target in self.get_implicit_roles_for_user(source)

    def _sever_routes_to(self, user, leads_to_target):
        """Remove the subject's direct grouping edges that lead to a target.

        ``leads_to_target`` is a predicate over the head of a ``g, user, head``
        edge; an edge is removed when its head either is, or transitively
        reaches, the access being revoked. Only edges originating at ``user``
        are removed, so no other subject's access is affected. Returns True if
        any edge was removed.
        """
        changed = False
        for rule in list(self.get_filtered_grouping_policy(0, user)):
            head = rule[1]
            if leads_to_target(head):
                if self.remove_grouping_policy(*rule):
                    changed = True
        return changed
