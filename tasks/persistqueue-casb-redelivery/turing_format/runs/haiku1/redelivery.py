"""Redelivery-limited ack queue with dead-lettering.

`RedeliveryAckQueue` extends :class:`persistqueue.sqlackqueue.SQLiteAckQueue`
with a per-item delivery-attempt limit. A normal ack queue redelivers a
``nack``-ed or crash-recovered item forever; a single "poison" message that
keeps failing can loop indefinitely. This queue caps the number of delivery
attempts per item: once an item has been delivered more than ``max_attempts``
times it is moved to a terminal dead-letter state instead of being made ready
again.

See ``docs/redelivery.md`` for the exact behavior, including how delivery
attempts must be counted across process restarts.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional

from persistqueue.sqlackqueue import SQLiteAckQueue, AckStatus
from persistqueue import sqlbase

log = logging.getLogger(__name__)


class DeadLetterStatus:
    """Status value for dead-lettered items."""
    dead_letter = '7'


class RedeliveryAckQueue(SQLiteAckQueue):
    """SQLite ack queue with delivery attempt tracking and dead-lettering.

    Extends SQLiteAckQueue to track delivery attempts per item and dead-letter
    items that have exhausted their maximum allowed delivery attempts.
    """

    _TABLE_NAME = 'redelivery_queue'
    _SQL_CREATE = (
        'CREATE TABLE IF NOT EXISTS {table_name} ('
        '{key_column} INTEGER PRIMARY KEY AUTOINCREMENT, '
        'data BLOB, timestamp FLOAT, status INTEGER, attempts INTEGER DEFAULT 0)'
    )

    def __init__(self, path: str, max_attempts: int = 5, **kwargs: Any) -> None:
        self.max_attempts = max_attempts
        super().__init__(path, **kwargs)

    def _pop(self, rowid: Optional[int] = None, next_in_order: bool = False,
             raw: bool = False):
        """Override _pop to record delivery attempts when item is fetched."""
        # Call parent's _pop to get item and mark as unack
        item = super()._pop(rowid=rowid, next_in_order=next_in_order, raw=raw)

        # If we got an item, record the delivery attempt
        if item is not None:
            if isinstance(item, dict) and "pqid" in item:
                item_id = item["pqid"]
            else:
                # For non-raw items, search the unack cache for ID
                item_id = self._find_item_id(item, search=True)

            if item_id is not None:
                self._increment_attempts(item_id)

        return item

    def nack(self, item: Any = None, id: Optional[int] = None) -> Optional[int]:
        """Return an item for redelivery, unless it has exhausted its
        delivery attempts, in which case dead-letter it instead."""
        item, search = self._check_id(item, id)
        with self.action_lock:
            _id = self._find_item_id(item, search)
            if _id is None:
                return None

            # Check if item has exhausted its attempts
            attempts = self._get_attempts(_id)
            if attempts > self.max_attempts:
                # Dead-letter the item
                self._mark_ack_status(_id, DeadLetterStatus.dead_letter)
                if _id in self._unack_cache:
                    self._unack_cache.pop(_id)
            else:
                # Requeue for redelivery
                self._mark_ack_status(_id, AckStatus.ready)
                if _id in self._unack_cache:
                    self._unack_cache.pop(_id)
                self.total += 1
        return _id

    def resume_unack_tasks(self) -> None:
        """Recover items left ``unack`` by a crashed process, counting the
        crashed delivery as an attempt and dead-lettering any item that has
        now exhausted its attempts."""
        unack_count = self.unack_count()
        if unack_count:
            log.info("resume %d unack tasks", unack_count)

        # Get all unack items before marking them
        sql = 'SELECT {} FROM {} WHERE status = ?'.format(
            self._key_column, self._table_name)
        with self.tran_lock:
            with self._getter as getter:
                unack_rows = getter.execute(sql, (AckStatus.unack,)).fetchall()

        # Increment attempts for each unack item and determine its fate
        with self.tran_lock:
            with self._putter as tran:
                for row in unack_rows:
                    item_id = row[0]
                    # Increment the attempt count
                    self._increment_attempts_direct(tran, item_id)
                    # Get updated attempt count
                    attempts = self._get_attempts_direct(tran, item_id)

                    if attempts > self.max_attempts:
                        # Dead-letter it
                        tran.execute(
                            'UPDATE {} SET status = ? WHERE {} = ?'.format(
                                self._table_name, self._key_column),
                            (DeadLetterStatus.dead_letter, item_id)
                        )
                    else:
                        # Make it ready for redelivery
                        tran.execute(
                            'UPDATE {} SET status = ? WHERE {} = ?'.format(
                                self._table_name, self._key_column),
                            (AckStatus.ready, item_id)
                        )
            self.total = self._count()

    def attempts(self, id: int) -> int:
        """Return the delivery-attempt count for an item id."""
        return self._get_attempts(id)

    def dead_letter_ids(self) -> List[int]:
        """Return the ids of items that have been dead-lettered."""
        sql = 'SELECT {} FROM {} WHERE status = ?'.format(
            self._key_column, self._table_name)
        with self.tran_lock:
            with self._getter as getter:
                rows = getter.execute(sql, (DeadLetterStatus.dead_letter,)).fetchall()
        return [row[0] for row in rows]

    def _increment_attempts(self, item_id: int) -> None:
        """Increment the attempt count for an item (thread-safe wrapper)."""
        with self.tran_lock:
            with self._putter as tran:
                self._increment_attempts_direct(tran, item_id)

    def _increment_attempts_direct(self, conn, item_id: int) -> None:
        """Increment the attempt count for an item using a given connection."""
        sql = 'UPDATE {} SET attempts = attempts + 1 WHERE {} = ?'.format(
            self._table_name, self._key_column)
        conn.execute(sql, (item_id,))

    def _get_attempts(self, item_id: int) -> int:
        """Get the attempt count for an item."""
        sql = 'SELECT attempts FROM {} WHERE {} = ?'.format(
            self._table_name, self._key_column)
        with self.tran_lock:
            with self._getter as getter:
                row = getter.execute(sql, (item_id,)).fetchone()
        return row[0] if row else 0

    def _get_attempts_direct(self, conn, item_id: int) -> int:
        """Get the attempt count for an item using a given connection."""
        sql = 'SELECT attempts FROM {} WHERE {} = ?'.format(
            self._table_name, self._key_column)
        row = conn.execute(sql, (item_id,)).fetchone()
        return row[0] if row else 0
