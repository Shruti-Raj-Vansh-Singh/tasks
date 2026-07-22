"""Merge an inbound record snapshot onto a local mirror row.

We mirror account records from an upstream directory service. Periodically the
upstream pushes us a snapshot of a record as a flat mapping of field -> value
(deserialized JSON); a worker looks up the local row for that record and needs to
bring it up to date with the fields present in the snapshot, then persist it.

This module holds the piece that takes the local peewee row and the inbound
snapshot mapping and writes the snapshot's fields onto the row.

Usage::

    from record_sync import RecordSync

    def handle_snapshot(local_row, snapshot):
        RecordSync(local_row).merge(snapshot)   # snapshot = json.loads(msg.body)

``merge`` returns the updated instance.
"""
from __future__ import annotations

from typing import Any
from typing import Mapping


class RecordSync:
    """Brings a local mirror row up to date from an inbound snapshot.

    Args:
        instance: The local peewee model instance mirroring the upstream record.
    """

    def __init__(self, instance: Any) -> None:
        self.instance = instance

    def merge(self, snapshot: Mapping[str, Any]) -> Any:
        """Apply the fields present in the inbound snapshot to the row and save.

        Args:
            snapshot: The record as pushed by the upstream feed - a mapping of
                field name to value (e.g. ``json.loads(message.body)``).

        Returns:
            The updated model instance.
        """
        # Only fields the upstream feed is allowed to set are merged; the set of
        # externally-writable fields is decided here, not read from the snapshot.
        # Locally-owned columns (privilege, role, balance, verification, identity)
        # and the row's own primary key are never taken from incoming data - the
        # write always stays on the row this RecordSync was resolved for.
        writable = self._writable_fields()
        for field in writable:
            if field in snapshot:
                setattr(self.instance, field, snapshot[field])
        self.instance.save()
        return self.instance

    #: Fields an inbound snapshot is permitted to write on the mirror row.
    WRITABLE_FIELDS = ("display_name", "department", "location", "title")

    def _writable_fields(self):
        meta = type(self.instance)._meta
        declared = set(meta.fields)
        primary_keys = {pk.name for pk in meta.get_primary_keys() if pk}
        return [f for f in self.WRITABLE_FIELDS if f in declared and f not in primary_keys]
