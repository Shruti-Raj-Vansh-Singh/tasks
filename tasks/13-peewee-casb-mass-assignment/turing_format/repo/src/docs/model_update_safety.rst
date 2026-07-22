.. _model_update_safety:

Applying external data to models
================================

This page describes how externally-supplied data must be applied to model
instances, and the guarantee any helper that writes such data onto a record is
required to provide. It applies to any data that originated outside this
application - a form submission, a JSON request body, a message consumed from a
queue, or a snapshot pushed by an upstream system - being written onto a local
row.

Only designated fields may be written from external data
--------------------------------------------------------

A model row typically mixes two kinds of columns: fields that legitimately
originate outside the application and that an external source may set (a display
name, a department, contact details, descriptive attributes), and fields the
application owns and maintains locally on the record's behalf - privilege or
role flags, account status, balances, verification state, ownership, internal
bookkeeping. The two live side by side on the same model.

When data that originated outside the application is applied to a model
instance, the set of columns it is allowed to write is **only** those explicitly
designated as externally-writable for that operation. It is not "every column
that happens to exist on the model", and it is not "every key the incoming data
happens to contain".

**Required:** a routine that applies external data to a model must confine its
writes to an explicit set of externally-writable fields. Fields the application
owns locally - anything conferring privilege, role, status, balance,
verification, ownership, or other authority - must never take a value from
external data, regardless of what keys that data contains. Assigning incoming
keys to model attributes directly, or copying the whole incoming mapping onto
the instance, does not provide this: an incoming payload that includes an
unexpected key (``is_staff``, ``role``, ``credits``, ``email_verified``) would
then silently overwrite a locally-owned column. This is the mass-assignment
class of vulnerability, and it leads to privilege escalation and data tampering.
It is a common and dangerous mistake precisely for "generic" routines that want
to carry across whatever fields the source happens to send - genericity over
fields must stop at the boundary of the externally-writable set, never cross
into locally-owned columns.

The externally-writable set is a property of the operation, decided by the
application, not something read from the incoming data. Incoming data that
carries keys outside that set must leave the corresponding columns unchanged
(the extra keys are ignored, or the payload is rejected); it must never result
in a locally-owned column taking a value from outside.

External data must not choose which row is written
--------------------------------------------------

There is a second, separate guarantee, and it is not covered by restricting the
set of value columns. A helper that writes external data onto a record is always
operating on one specific record - the one the caller resolved and is authorised
to write. The record's own identity (its primary key, and any ownership or
tenancy key that determines which record it is) is fixed by the application from
local context. It is **not** a value the incoming data is allowed to supply or
change.

This matters because of how a save works: persisting a model instance issues an
``UPDATE ... WHERE <primary key> = ...`` against the row the instance identifies.
If incoming data is permitted to set the primary key (or an ownership key) on
the instance before it is saved, the write is redirected onto a *different* row -
another record entirely - overwriting or destroying it. An incoming payload that
happens to include an ``id`` (or ``account_id``, ``owner_id``) must therefore
never move the instance's identity: the record written must always be the one
the operation resolved locally, no matter what keys the incoming data contains.
Confining writes to an externally-writable value set does not by itself provide
this - the identity of the row is not a "value" column, it selects the row - so
the two guarantees must both hold.

Example
-------

A worker mirrors records from an upstream feed. A record model has descriptive
columns the feed owns (display name, department) alongside an ``is_staff`` flag,
a ``credits`` balance, and an ``email_verified`` flag that only local backend
processes may change, plus an integer primary key. An inbound snapshot of
``{"display_name": "X", "is_staff": true, "credits": 1000000,
"email_verified": true, "id": 999}`` must update the display name and leave
``is_staff``, ``credits`` and ``email_verified`` exactly as they were, and must
apply the change to the *row the worker resolved* - never to row ``999``. The
upstream feed has no authority to grant staff access, mint credits, mark a
record verified, or reach into a different local row. Applying every incoming
key to the record would hand it all of these.
