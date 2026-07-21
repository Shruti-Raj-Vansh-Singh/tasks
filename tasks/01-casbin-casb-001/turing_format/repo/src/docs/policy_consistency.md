# Policy Consistency Guarantee

This page documents a hard behavioral guarantee that every enforcer in this
library must uphold. It applies to `Enforcer` and to any subclass or wrapper
that changes how a decision is produced.

## Read-after-write

An authorization decision returned by `enforce()` must always reflect the
policy state that exists at the moment `enforce()` is called.

Concretely, once a management call has returned, the very next `enforce()` call
must observe its effect:

- After a rule that granted access is removed, `enforce()` for that access
  must return `False`.
- After a rule that grants access is added, `enforce()` for that access must
  return `True`.

There is no "eventual consistency" window. Casbin is used to gate access to
real resources, so a decision that lags behind the current policy is a
security defect, not merely a staleness issue: it can allow a request that the
current policy forbids, or deny a request that the current policy permits.

## Every mutation path counts

The policy is changed by more than one API family, and the guarantee applies to
**all** of them equally. A decision must never survive any of the following:

- Direct permission edits: `add_policy`, `remove_policy`, `add_named_policy`,
  `remove_named_policy`, and the `*_ex` / batch variants.
- Filtered edits: `remove_filtered_policy`, `update_policy`,
  `update_filtered_policies`.
- Role / grouping edits: `add_role_for_user`, `delete_role_for_user`,
  `delete_roles_for_user`, `delete_user`, `delete_role`,
  `add_grouping_policy`, `remove_grouping_policy`. These change role
  inheritance (`g`) rather than permissions (`p`), but they change the decision
  just the same.
- Bulk resets and reloads: `clear_policy`, `load_policy`,
  `load_filtered_policy`, and building or rebuilding role links.

Role edits deserve special attention. Because roles are transitive, revoking a
single link can change the decision for a subject that is not even named in the
edited rule. For example, if `alice` inherits `admin` through `manager` and the
`manager -> admin` link is revoked, then `alice`'s access that depended on
`admin` must immediately become `False`, even though the revoked rule mentions
only `manager` and `admin`.

## Rationale

Applications frequently revoke access and expect it to take effect
immediately: an admin disables a compromised account, an operator pulls a role
during an incident, a subscription lapses. If any decision path can return a
value that predates such a change, the system keeps honoring access that has
already been taken away. Treat a stale allow as a privilege-escalation bug.

## A note for cached decisions

Any component that memoizes decisions may keep entries warm across an edit for
performance, but only entries the edit cannot change. Deciding which cached
entries an edit *can* change must account for role inheritance: because a
grant on a role is inherited by every user who transitively holds that role, a
change to a role -- or to a permission attached to a role -- can invalidate
decisions for subjects that are not named anywhere in the changed rule.
Correctness of the guarantee above always takes precedence over cache hit
rate.
