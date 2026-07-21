from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable

    from queuelib.queue import BaseQueue


class FairPriorityQueue:
    """A priority queue that shares turns fairly across *keys* within a
    priority level.

    Like :class:`~queuelib.pqueue.PriorityQueue`, items have an integer
    priority (lower number = higher priority) and higher-priority items are
    served before lower-priority ones. In addition, each item has a ``key``
    (for example a source or domain). Within a single priority level, when
    several keys have items ready, :meth:`pop` spreads turns across those
    keys instead of draining one key before moving to the next, so a noisy
    key cannot starve the others at the same priority.

    The constructor receives a ``qfactory`` callable used to create a new
    internal queue for a ``(priority, key)`` bucket; it is called with the
    priority and key. The internal queue must implement ``push``, ``pop``,
    ``peek``, ``close`` and ``__len__`` (e.g. ``FifoMemoryQueue``).

    See ``docs/fair_priority_queue.md`` for the exact ordering behavior this
    class must provide.
    """

    def __init__(self, qfactory: Callable[[int, Hashable], BaseQueue]) -> None:
        self.qfactory = qfactory
        # One internal FIFO queue per (priority, key) bucket.
        self.queues: dict[tuple[int, Hashable], BaseQueue] = {}
        # For each priority, the keys with items ready, in round-robin order.
        # A key is present here if and only if its bucket is non-empty.
        self.key_queues: dict[int, deque[Hashable]] = {}

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        bucket = (priority, key)
        if bucket not in self.queues:
            self.queues[bucket] = self.qfactory(priority, key)
        q = self.queues[bucket]
        q.push(obj)  # this may fail (eg. serialization error)
        # Register the key for round-robin only after a successful push, so a
        # failed push never leaves an empty bucket in the rotation.
        keys = self.key_queues.setdefault(priority, deque())
        if key not in keys:
            keys.append(key)

    def pop(self) -> Any | None:
        if not self.key_queues:
            return None
        # Strict priority: always serve the highest-priority (lowest-numbered)
        # level that currently has items, recomputed on every pop so a later
        # higher-priority push is never delayed by fairness rotation.
        priority = min(self.key_queues)
        keys = self.key_queues[priority]
        key = keys.popleft()
        bucket = (priority, key)
        q = self.queues[bucket]
        m = q.pop()
        if len(q) == 0:
            del self.queues[bucket]
            q.close()
        else:
            # Rotate the key to the back so the next pop tries the other keys.
            keys.append(key)
        if not keys:
            del self.key_queues[priority]
        return m

    def peek(self) -> Any | None:
        if not self.key_queues:
            return None
        priority = min(self.key_queues)
        key = self.key_queues[priority][0]
        return self.queues[priority, key].peek()

    def close(self) -> list[tuple[int, Hashable]]:
        active = []
        for bucket, q in self.queues.items():
            if len(q):
                active.append(bucket)
            q.close()
        return active

    def __len__(self) -> int:
        return sum(len(q) for q in self.queues.values())
