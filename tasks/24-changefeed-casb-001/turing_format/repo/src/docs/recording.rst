Recording account changes
==========================

The activity feed shows account admins what changed on their team's account
records over time. Each edit to a record produces one **feed entry** that the
dashboard renders in a chronological list and includes in the weekly summary
email.

The record shape
----------------

An account record is a JSON-like dict. It always has an ``account_id`` and an
``owner`` sub-object (with at least a ``display_name``), plus whatever plan,
status and profile fields the account carries. Records may be nested.

Two snapshots
-------------

``record_change`` is called with the *previous* snapshot of a record and the
*current* one. Both snapshots have the same shape; the job is to describe how
the current one differs from the previous one.

Computing the difference with ``dictdiffer``
--------------------------------------------

``dictdiffer.diff(old, new)`` returns an iterator of ``(kind, path, values)``
tuples:

.. code-block:: pycon

    >>> import dictdiffer
    >>> old = {"plan": "free", "seats": 3}
    >>> new = {"plan": "pro", "seats": 3}
    >>> list(dictdiffer.diff(old, new))
    [('change', 'plan', ('free', 'pro'))]

- ``kind`` is ``"change"``, ``"add"`` or ``"remove"``.
- ``path`` is the key (or a dotted/list path for nested keys) that changed.
- ``values`` is ``(old_value, new_value)`` for a change, or a list of
  ``(key, value)`` pairs for adds/removes.

The entry
---------

Build one entry per call and append it to the feed:

.. code-block:: python

    entry = {
        "account": new_record["account_id"],
        "owner": new_record["owner"]["display_name"],
        "changes": <a description of what changed>,
    }

Return the appended entry. When the two snapshots are identical there is nothing
to show, so append nothing and return ``{}``.
