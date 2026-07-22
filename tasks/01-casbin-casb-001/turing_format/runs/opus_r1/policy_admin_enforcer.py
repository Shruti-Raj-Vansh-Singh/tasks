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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def apply_permission_changeset(self, changeset):
        """Apply a batch of grant/revoke directives and report what happened.

        ``changeset`` is a list of directive dicts (see the class docstring).
        Every directive is applied to the underlying policy, in order, and a
        JSON-serializable summary dict is returned with the keys ``applied``,
        ``granted``, ``revoked`` and ``results``.

        The report is stated in terms of *access*, not rules touched
        (``docs/policy_administration.md``). A grant is reported as ``granted``
        only when the named subject actually ends up with the named access; a
        revoke is reported as ``removed`` only when, afterwards, the subject
        genuinely no longer has that access. A subject that can reach the same
        access by more than one route still has it until every route is gone,
        so a revoke that only tore down one of several routes is reported
        truthfully as *not* removed rather than claimed as a success.
        """
        results = []
        granted = 0
        revoked = 0
        applied = 0

        for index, directive in enumerate(changeset):
            result = self._apply_directive(index, directive)
            results.append(result)

            if result["op"] == "grant":
                granted += 1
            elif result["op"] == "revoke":
                revoked += 1

            if result.get("changed"):
                applied += 1

        return {
            "applied": applied,
            "granted": granted,
            "revoked": revoked,
            "results": results,
        }

    def _apply_directive(self, index, directive):
        """Apply a single directive and return its per-directive result dict."""
        if not isinstance(directive, dict):
            raise ValueError("changeset directive at index %d is not a dict: %r" % (index, directive))

        op = directive.get("op")
        dtype = directive.get("type")
        user = directive.get("user")

        if op not in ("grant", "revoke"):
            raise ValueError("changeset directive at index %d has invalid 'op': %r" % (index, op))
        if dtype not in ("role", "permission"):
            raise ValueError("changeset directive at index %d has invalid 'type': %r" % (index, dtype))
        if not user:
            raise ValueError("changeset directive at index %d is missing 'user'" % index)

        if dtype == "role":
            return self._apply_role_directive(index, op, user, directive)
        return self._apply_permission_directive(index, op, user, directive)

    def _apply_role_directive(self, index, op, user, directive):
        role = directive.get("role")
        if not role:
            raise ValueError("role directive at index %d is missing 'role'" % index)

        result = {
            "index": index,
            "op": op,
            "type": "role",
            "user": user,
            "role": role,
        }

        if op == "grant":
            changed = self.add_role_for_user(user, role)
            # The named access is membership of `role`: confirm the subject
            # ends up holding it (directly or through the role graph).
            has_role = self._user_has_role(user, role)
            result["changed"] = bool(changed)
            result["granted"] = bool(has_role)
            result["ok"] = bool(has_role)
        else:
            changed = self.delete_role_for_user(user, role)
            # Truthful revoke report: only claim removal when the subject no
            # longer has the role after the edit. If they reach it by another
            # route (e.g. a role chain), it was not actually removed.
            still_has_role = self._user_has_role(user, role)
            result["changed"] = bool(changed)
            result["removed"] = not still_has_role
            result["ok"] = not still_has_role

        return result

    def _apply_permission_directive(self, index, op, user, directive):
        perm = directive.get("perm")
        if not perm or not isinstance(perm, (list, tuple)):
            raise ValueError("permission directive at index %d needs a non-empty 'perm' list" % index)
        perm = list(perm)

        result = {
            "index": index,
            "op": op,
            "type": "permission",
            "user": user,
            "perm": perm,
        }

        if op == "grant":
            changed = self.add_permission_for_user(user, *perm)
            # The named access is (user, *perm): confirm enforce() now allows it.
            allowed = self.enforce(user, *perm)
            result["changed"] = bool(changed)
            result["granted"] = bool(allowed)
            result["ok"] = bool(allowed)
        else:
            changed = self.delete_permission_for_user(user, *perm)
            # Truthful revoke report: enforce() is the sole authority on whether
            # the subject still has the access. Removing the direct rule does not
            # remove access held through a shared role, so only report removal
            # when enforce() actually returns False.
            still_allowed = self.enforce(user, *perm)
            result["changed"] = bool(changed)
            result["removed"] = not still_allowed
            result["ok"] = not still_allowed

        return result

    def _user_has_role(self, user, role):
        """Whether ``user`` holds ``role`` directly or through the role graph."""
        if self.has_role_for_user(user, role):
            return True
        return role in self.get_implicit_roles_for_user(user)
