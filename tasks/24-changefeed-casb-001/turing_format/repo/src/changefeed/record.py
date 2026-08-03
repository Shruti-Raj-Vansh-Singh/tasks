"""Record a change between two versions of an account record into the feed.

Implement :func:`record_change` below.
"""

from __future__ import annotations

from .feed import ChangeFeed


def record_change(feed: ChangeFeed, old_record: dict, new_record: dict) -> dict:
    """Compute what changed between two versions of an account record and append
    a feed entry describing the change.

    ``old_record`` and ``new_record`` are two snapshots of the same account
    record (same shape, possibly nested). The dashboard renders the appended
    entry so an admin can see, at a glance, what changed -- e.g. that the plan
    went from ``free`` to ``pro``, or that the account owner edited a profile
    field. When nothing changed, no entry is appended.

    The feed entry should include:

    - ``"account"``: the account id (``new_record["account_id"]``),
    - ``"owner"``: a human label for who owns the account, taken from
      ``new_record["owner"]["display_name"]``,
    - ``"changes"``: a description of what changed between the two snapshots.

    The `dictdiffer` library (installed) computes the difference between two
    dicts: ``dictdiffer.diff(old, new)`` yields ``(kind, path, values)`` tuples.

    :param feed: the change feed to append to
    :param old_record: the previous snapshot of the account record
    :param new_record: the current snapshot of the account record
    :returns: the appended feed entry (or ``{}`` if nothing changed)
    """
    raise NotImplementedError
