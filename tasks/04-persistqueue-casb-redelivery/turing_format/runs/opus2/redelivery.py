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

from typing import Any, List, Optional

from persistqueue import sqlbase
from persistqueue.sqlackqueue import AckStatus, SQLiteAckQueue


class RedeliveryAckQueue(SQLiteAckQueue):
    # Own table so a redelivery queue never shares state with a plain
    # SQLiteAckQueue on the same path. The extra ``attempts`` column stores
    # the delivery-attempt count durably alongside the item itself, so it
    # survives process restarts (see docs/redelivery.md).
    _TABLE_NAME = 'ack_redelivery_queue'
    _SQL_CREATE = (
        'CREATE TABLE IF NOT EXISTS {table_name} ('
        '{key_column} INTEGER PRIMARY KEY AUTOINCREMENT, '
        'data BLOB, timestamp FLOAT, status INTEGER, '
        'attempts INTEGER NOT NULL DEFAULT 0)'
    )

    # Terminal dead-letter status. Any value ``>= AckStatus.unack`` is never
    # selected for delivery nor counted as ready/unack, and it must not clash
    # with the existing acked/ack_failed states.
    DEAD_LETTER = '8'

    def __init__(
        self, path: str, max_attempts: int = 5, **kwargs: Any
    ) -> None:
        self.max_attempts = max_attempts
        super().__init__(path, **kwargs)

    def get(
        self, block: bool = True, timeout: Optional[float] = None,
        id: Optional[int] = None, next_in_order: bool = False,
        raw: bool = False,
    ) -> Any:
        """Deliver the next ready item, recording a delivery attempt for it.

        The attempt is persisted before the item is handed out, so a worker
        that crashes while processing has already had this delivery counted.
        """
        # Fetch raw so we always know the item's id, then reshape the result
        # to honour the caller's ``raw`` request.
        item = super().get(
            block=block, timeout=timeout, id=id,
            next_in_order=next_in_order, raw=True,
        )
        self._increment_attempts(item['pqid'])
        return item if raw else item['data']

    def nack(
        self, item: Any = None, id: Optional[int] = None
    ) -> Optional[int]:
        """Return an item for redelivery, unless it has exhausted its
        delivery attempts, in which case dead-letter it instead."""
        item, search = self._check_id(item, id)
        with self.action_lock:
            _id = self._find_item_id(item, search)
            if _id is None:
                return None
            if self.attempts(_id) > self.max_attempts:
                # Exhausted: move to the terminal dead-letter state and do
                # not make it ready again.
                self._mark_ack_status(_id, self.DEAD_LETTER)
                self._unack_cache.pop(_id, None)
            else:
                self._mark_ack_status(_id, AckStatus.ready)
                self._unack_cache.pop(_id, None)
                self.total += 1
        return _id

    def resume_unack_tasks(self) -> None:
        """Recover items left ``unack`` by a crashed process, counting the
        crashed delivery as an attempt and dead-lettering any item that has
        now exhausted its attempts.

        The crashed delivery's attempt was already recorded durably by
        ``get`` before the item was handed out, so recovery only has to
        decide, per item, between redelivery and dead-lettering.
        """
        with self.tran_lock:
            with self._putter as tran:
                # Dead-letter unack items that are now out of attempts.
                tran.execute(
                    'UPDATE {} SET status = ? '
                    'WHERE status = ? AND attempts > ?'
                    .format(self._table_name),
                    (self.DEAD_LETTER, AckStatus.unack, self.max_attempts),
                )
                # Make the remaining unack items ready for redelivery.
                tran.execute(
                    'UPDATE {} SET status = ? WHERE status = ?'
                    .format(self._table_name),
                    (AckStatus.ready, AckStatus.unack),
                )
            self.total = self._count()

    def attempts(self, id: int) -> int:
        """Return the delivery-attempt count for an item id."""
        sql = 'SELECT attempts FROM {} WHERE {} = ?'.format(
            self._table_name, self._key_column
        )
        row = self._getter.execute(sql, (id,)).fetchone()
        return row[0] if row else 0

    def dead_letter_ids(self) -> List[int]:
        """Return the ids of items that have been dead-lettered."""
        sql = 'SELECT {} FROM {} WHERE status = ?'.format(
            self._key_column, self._table_name
        )
        rows = self._getter.execute(sql, (self.DEAD_LETTER,)).fetchall()
        return [row[0] for row in rows]

    @sqlbase.with_conditional_transaction
    def _increment_attempts(self, id: int) -> Any:
        sql = 'UPDATE {} SET attempts = attempts + 1 WHERE {} = ?'.format(
            self._table_name, self._key_column
        )
        return sql, (id,)
