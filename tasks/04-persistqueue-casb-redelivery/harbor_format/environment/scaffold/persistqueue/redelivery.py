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

from persistqueue.sqlackqueue import SQLiteAckQueue


class RedeliveryAckQueue(SQLiteAckQueue):
    def __init__(self, path: str, max_attempts: int = 5, **kwargs: Any) -> None:
        self.max_attempts = max_attempts
        super().__init__(path, **kwargs)

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """Deliver the next ready item, recording a delivery attempt for it."""
        raise NotImplementedError("RedeliveryAckQueue.get is not implemented yet")

    def nack(self, item: Any = None, id: Optional[int] = None) -> Optional[int]:
        """Return an item for redelivery, unless it has exhausted its
        delivery attempts, in which case dead-letter it instead."""
        raise NotImplementedError("RedeliveryAckQueue.nack is not implemented yet")

    def resume_unack_tasks(self) -> None:
        """Recover items left ``unack`` by a crashed process, counting the
        crashed delivery as an attempt and dead-lettering any item that has
        now exhausted its attempts."""
        raise NotImplementedError(
            "RedeliveryAckQueue.resume_unack_tasks is not implemented yet"
        )

    def attempts(self, id: int) -> int:
        """Return the delivery-attempt count for an item id."""
        raise NotImplementedError("RedeliveryAckQueue.attempts is not implemented yet")

    def dead_letter_ids(self) -> List[int]:
        """Return the ids of items that have been dead-lettered."""
        raise NotImplementedError(
            "RedeliveryAckQueue.dead_letter_ids is not implemented yet"
        )
