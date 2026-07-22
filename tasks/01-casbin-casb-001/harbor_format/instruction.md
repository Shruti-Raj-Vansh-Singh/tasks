We use pycasbin for authorization across a few services, and access rules are
owned upstream: an IAM/HR system is the source of truth, and a sync job pushes
role and permission changes down to each service. Right now that sync job calls
the casbin management API one edit at a time and has grown a lot of fiddly
bookkeeping about what to apply and in what order. I want to move that logic
behind one clean entry point so the sync job can just hand us the whole batch.

I started a class for this and ran out of time. It's in
`casbin/policy_admin_enforcer.py` as `PolicyAdminEnforcer`, it subclasses
`Enforcer`, and it's already exported from `casbin/__init__.py`. I need you to
implement `apply_permission_changeset(self, changeset)`.

A changeset is a list of directives. Each directive is a plain dict with an
`"op"` of `"grant"` or `"revoke"` and a `"type"` of `"role"` or `"permission"`:

- role directive:
  `{"op": "grant",  "type": "role", "user": "alice", "role": "admin"}`
  `{"op": "revoke", "type": "role", "user": "alice", "role": "admin"}`
  (the `"user"` field may itself be a role name - that's how a role hierarchy is
  expressed, e.g. giving the `support` role the `admin` role.)
- permission directive:
  `{"op": "grant",  "type": "permission", "user": "alice", "perm": ["data1", "read"]}`
  `{"op": "revoke", "type": "permission", "user": "alice", "perm": ["data1", "read"]}`

Concretely I want:

- `apply_permission_changeset(changeset)` applies every directive to the policy
  and returns a JSON-serializable summary dict. Please include `applied`,
  `granted`, `revoked`, and a `results` list with one entry per directive. A
  caller reads the summary to confirm what happened - in particular, for a
  revoke, whether the access it named was actually taken away.
- After a changeset is applied, `enforce(...)` should reflect the access each
  subject is meant to have as a result of that changeset.
- Don't change the behavior of the base `Enforcer` for anything a changeset
  doesn't touch, and keep the existing test suite passing.
- Standard library and pycasbin only - no third-party dependencies.

There's a short note on what the team relies on from a policy change in
`docs/policy_administration.md`; it's the context I'd give a new teammate
picking this up.

Please also add focused tests in `tests/test_policy_admin_enforcer.py`. There
are already some tests under `tests/utility/` you can follow for style and for
the model/policy fixtures. Cover granting a role and a permission, revoking a
role and a permission for the straightforward case, and that the returned
summary lines up with what actually happened.
