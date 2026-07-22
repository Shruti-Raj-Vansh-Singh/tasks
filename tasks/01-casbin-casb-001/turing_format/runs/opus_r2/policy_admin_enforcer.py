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
        """Apply a batch of grant/revoke directives and return a summary.

        Each directive in ``changeset`` is applied in order to the running
        policy. The returned dict is JSON-serializable and has the keys:

        * ``"applied"`` - number of directives that changed the policy,
        * ``"granted"`` / ``"revoked"`` - per-op counts of directives that
          changed the policy,
        * ``"results"`` - one entry per directive, in the same order as the
          changeset.

        Each ``results`` entry is a dict with at least ``"op"``, ``"type"``,
        ``"changed"`` (whether the underlying policy was modified) and
        ``"ok"`` (whether the directive achieved its intent). For a revoke it
        additionally carries ``"removed"``: whether, *after* the apply, the
        named subject genuinely no longer has the named access. ``"removed"``
        is decided by asking the enforcer, not by whether a rule was deleted -
        a subject that still reaches the access by another route (a direct
        grant alongside a role, or a second role chain) is reported as *not*
        removed, because it can still exercise the access.
        """
        results = []
        applied = 0
        granted = 0
        revoked = 0

        for directive in changeset:
            result = self._apply_directive(directive)
            results.append(result)

            if result.get("changed"):
                applied += 1
                if result["op"] == "grant":
                    granted += 1
                elif result["op"] == "revoke":
                    revoked += 1

        return {
            "applied": applied,
            "granted": granted,
            "revoked": revoked,
            "results": results,
        }

    def _apply_directive(self, directive):
        """Apply one directive and return its per-directive result dict."""
        op = directive.get("op")
        dtype = directive.get("type")

        if op not in ("grant", "revoke"):
            raise ValueError("directive 'op' must be 'grant' or 'revoke', got %r" % (op,))
        if dtype not in ("role", "permission"):
            raise ValueError("directive 'type' must be 'role' or 'permission', got %r" % (dtype,))

        if dtype == "role":
            if op == "grant":
                return self._grant_role(directive)
            return self._revoke_role(directive)
        else:
            if op == "grant":
                return self._grant_permission(directive)
            return self._revoke_permission(directive)

    # -- role directives ----------------------------------------------------

    def _grant_role(self, directive):
        user = directive["user"]
        role = directive["role"]

        changed = self.add_role_for_user(user, role)
        # A grant confers what it names: the subject now has the role, whether
        # the link is new or was already present.
        has_role = self.has_role_for_user(user, role)

        return {
            "op": "grant",
            "type": "role",
            "user": user,
            "role": role,
            "changed": bool(changed),
            "ok": bool(has_role),
        }

    def _revoke_role(self, directive):
        user = directive["user"]
        role = directive["role"]

        changed = self.delete_role_for_user(user, role)
        # "The subject no longer has the role" is a statement about the
        # subject's membership, not about the single link we deleted: a
        # subject that still reaches the role through another chain has not
        # had it revoked. Ask the enforcer's role resolution, not the raw
        # grouping policy.
        removed = role not in self.get_implicit_roles_for_user(user)

        return {
            "op": "revoke",
            "type": "role",
            "user": user,
            "role": role,
            "changed": bool(changed),
            "removed": bool(removed),
            "ok": bool(removed),
        }

    # -- permission directives ---------------------------------------------

    def _grant_permission(self, directive):
        user = directive["user"]
        perm = list(directive["perm"])

        changed = self.add_permission_for_user(user, *perm)
        # After a grant the subject has the access; confirm via enforce so the
        # report reflects reachable access, not merely that a rule was written.
        has_access = self.enforce(user, *perm)

        return {
            "op": "grant",
            "type": "permission",
            "user": user,
            "perm": perm,
            "changed": bool(changed),
            "ok": bool(has_access),
        }

    def _revoke_permission(self, directive):
        user = directive["user"]
        perm = list(directive["perm"])

        # Remove the subject's direct route to the named access.
        changed = self.delete_permission_for_user(user, *perm)

        # A revoke is a statement about the subject's access, not about the
        # one rule we deleted. The subject may still reach exactly this access
        # through a role (or a chain of roles); if so it has NOT been revoked.
        # We only report the access as removed when the enforcer, after the
        # edit, agrees the subject can no longer exercise it - a report that
        # claimed removal while the subject still had access would tell the
        # operator something untrue.
        removed = not self.enforce(user, *perm)

        return {
            "op": "revoke",
            "type": "permission",
            "user": user,
            "perm": perm,
            "changed": bool(changed),
            "removed": bool(removed),
            "ok": bool(removed),
        }
