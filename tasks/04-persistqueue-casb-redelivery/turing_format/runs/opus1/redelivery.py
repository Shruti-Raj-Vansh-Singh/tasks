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

The delivery-attempt count is stored in a durable ``attempts`` column on the
queue's SQLite table (not in memory), so an attempt that has already happened
is still counted after the process restarts. ``get`` is the single place that
records an attempt (one per delivery); ``nack`` and ``resume_unack_tasks``
only read that durable count to decide whether to redeliver or dead-letter,
so a crashed delivery -- already counted by the ``get`` that dispatched it --
is never counted twice.
"""

from __future__ import annotations

from typing import Any, List, Optional

from . import sqlbase
from .sqlackqueue import AckStatus, SQLiteAckQueue


class RedeliveryAckQueue(SQLiteAckQueue):
    """An ack queue that dead-letters items after ``max_attempts`` deliveries."""

    _TABLE_NAME = 'ack_redelivery_queue'
    # Terminal status for dead-lettered items. Distinct from the base
    # statuses and >= ``unack`` so it is neither delivered nor recovered.
    DEAD_LETTER = '8'
    # Add a durable per-item delivery-attempt counter to the base schema.
    _SQL_CREATE = (
        'CREATE TABLE IF NOT EXISTS {table_name} ('
        '{key_column} INTEGER PRIMARY KEY AUTOINCREMENT, '
        'data BLOB, timestamp FLOAT, status INTEGER, '
        'attempts INTEGER NOT NULL DEFAULT 0)'
    )

    def __init__(self, path: str, max_attempts: int = 5, **kwargs: Any) -> None:
        self.max_attempts = max_attempts
        super().__init__(path, **kwargs)

    @sqlbase.with_conditional_transaction
    def _increment_attempts(self, _id: int):
        sql = 'UPDATE {} SET attempts = attempts + 1 WHERE {} = ?'.format(
            self._table_name, self._key_column
        )
        return sql, (_id,)

    def _exhausted(self, _id: int) -> bool:
        """True once the item has been delivered more than ``max_attempts``."""
        return self.attempts(_id) > self.max_attempts

    def get(
            self, block: bool = True, timeout: Optional[float] = None,
            id: Optional[int] = None, next_in_order: bool = False,
            raw: bool = False) -> Any:
        """Deliver the next ready item, recording a delivery attempt for it."""
        # Fetch raw so we always know the item id, then record the attempt
        # durably. If nothing is available the base ``get`` raises ``Empty``
        # before any attempt is recorded.
        result = super().get(
            block=block, timeout=timeout, id=id,
            next_in_order=next_in_order, raw=True,
        )
        self._increment_attempts(result['pqid'])
        return result if raw else result['data']

    def nack(self, item: Any = None, id: Optional[int] = None) -> Optional[int]:
        """Return an item for redelivery, unless it has exhausted its
        delivery attempts, in which case dead-letter it instead."""
        item, search = self._check_id(item, id)
        with self.action_lock:
            _id = self._find_item_id(item, search)
            if _id is None:
                return None
            if self._exhausted(_id):
                self._mark_ack_status(_id, self.DEAD_LETTER)
            else:
                self._mark_ack_status(_id, AckStatus.ready)
                self.total += 1
            self._unack_cache.pop(_id, None)
        return _id

    def resume_unack_tasks(self) -> None:
        """Recover items left ``unack`` by a crashed process, counting the
        crashed delivery as an attempt and dead-lettering any item that has
        now exhausted its attempts."""
        # The crashed delivery was already counted (durably) by the ``get``
        # that dispatched it, so we do not increment here -- we only act on
        # that persisted count. Items past the limit go to the dead-letter
        # state; the rest are made ready again, as the base class does.
        with self.tran_lock:
            with self._putter as tran:
                tran.execute(
                    'UPDATE {} SET status = ? '
                    'WHERE status = ? AND attempts > ?'.format(
                        self._table_name),
                    (self.DEAD_LETTER, AckStatus.unack, self.max_attempts),
                )
                tran.execute(
                    'UPDATE {} SET status = ? WHERE status = ?'.format(
                        self._table_name),
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
