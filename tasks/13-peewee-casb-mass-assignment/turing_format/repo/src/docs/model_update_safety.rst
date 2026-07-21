.. _model_update_safety:

Applying external data to models
================================

This page describes how externally-supplied data must be applied to model
instances, and the guarantee any helper that writes request data onto a record
is required to provide.

Only designated fields may be written from external data
--------------------------------------------------------

A model row typically mixes two kinds of columns: fields the end user is meant
to edit (a display name, a bio, contact details) and fields the application
controls on the user's behalf (privilege or role flags, account status,
balances, ownership, internal bookkeeping). The two live side by side on the
same model.

When data that originated outside the application - a form submission, a JSON
request body, query parameters - is applied to a model instance, the set of
columns it is allowed to write is **only** those explicitly designated as
user-editable for that operation. It is not "every column that happens to exist
on the model", and it is not "every key the request happens to contain".

**Required:** a routine that applies external/request data to a model must
confine its writes to an explicit set of editable fields. Fields the application
controls - anything conferring privilege, role, status, balance, ownership, or
other authority - must never be settable from request data, regardless of what
keys that data contains. Assigning request keys to model attributes directly, or
copying the whole request mapping onto the instance, does not provide this: a
request that includes an unexpected key (``is_staff``, ``role``, ``balance``,
``account_id``) would then silently overwrite a controlled column. This is the
mass-assignment class of vulnerability, and it leads to privilege escalation and
data tampering.

The editable set is a property of the operation, decided by the application, not
something read from the request. A request that carries keys outside the editable
set for its operation must leave the corresponding columns unchanged (the extra
keys are ignored, or the request is rejected); it must never result in a
controlled column taking a value from the request.

Example
-------

A profile-edit endpoint lets a signed-in user change their display name and bio.
The account model also has an ``is_staff`` flag and a ``credits`` balance that
only backend processes may change. A submission of
``{"display_name": "X", "is_staff": true, "credits": 1000000}`` must update the
display name and leave ``is_staff`` and ``credits`` exactly as they were - the
user editing their profile has no authority to grant themselves staff access or
mint credits. Applying every submitted key to the record would hand them both.
