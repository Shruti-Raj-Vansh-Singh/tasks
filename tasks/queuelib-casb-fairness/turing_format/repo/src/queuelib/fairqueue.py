from __future__ import annotations

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
        raise NotImplementedError("FairPriorityQueue is not implemented yet")

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        raise NotImplementedError("FairPriorityQueue.push is not implemented yet")

    def pop(self) -> Any | None:
        raise NotImplementedError("FairPriorityQueue.pop is not implemented yet")

    def peek(self) -> Any | None:
        raise NotImplementedError("FairPriorityQueue.peek is not implemented yet")

    def __len__(self) -> int:
        raise NotImplementedError("FairPriorityQueue.__len__ is not implemented yet")
