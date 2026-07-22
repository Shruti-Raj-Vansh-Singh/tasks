# Runtime policy administration

pycasbin lets an application change its policy while the process is running:
roles are granted and revoked, permissions are added and removed, and rules
are loaded from a store. Many deployments drive these changes from an upstream
system of record - an HR directory, an IAM export, a ticket - and apply them in
batches.

This page describes what an application should be able to rely on after a
policy change is applied, so that a decision returned by `enforce()` always
matches the access the operator actually intended.

## Access is what `enforce()` answers, not which rule was edited

`enforce(sub, obj, act)` answers one question: *does this subject currently
have this access?* In an RBAC model that answer follows every route the subject
has to a permission - a permission held directly, a permission held through a
role, and a permission held through a chain of roles (`g, alice, manager`
together with `g, manager, admin` means `alice` has everything `admin` has).
Two subjects can reach the same permission through completely different routes,
and one subject can reach the same permission through more than one route at
once.

Because access is defined this way, the guarantees below are stated in terms of
the access a subject *ends up with* after a change is applied - not in terms of
whether a particular rule was added or deleted.

## Grants

After a grant is applied, the named subject has the named access: `enforce()`
returns `True` for it.

A grant confers only what it names. It does not change the access of any
subject the directive did not mention.

## Revocations

A revocation means the named subject no longer has the named access. After a
revoke is applied, `enforce()` for that access returns `False`.

"The subject no longer has the access" is a statement about the subject's
access, not about any single rule. A subject that reached the access by more
than one route still has it until every route is gone; deleting one rule that
mentioned the access is not the same as removing the access.

## The end state is what the operator asked for

A change is applied so that the running policy reflects the operator's
intended end state. When several directives are applied together, the intended
end state is the one they describe as a whole: a directive that removes access
expresses an intent to take that access away, and that intent is part of the
end state the operator expects to see once everything has been applied.

## What a change reports

An apply reports what it did, and the report is about access, not about rules
touched. A directive that removes access may be reported as having done so only
when, afterward, the subject genuinely no longer has that access. A report that
says access was removed while the subject can still exercise it tells the
operator something untrue and is worse than no report at all.
