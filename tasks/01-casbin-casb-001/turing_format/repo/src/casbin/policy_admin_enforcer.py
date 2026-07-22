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
        raise NotImplementedError("PolicyAdminEnforcer is not implemented yet")
