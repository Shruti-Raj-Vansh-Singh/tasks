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
        # priority -> {key: internal queue}; every registered bucket is
        # non-empty and its key is also present in ``self.order[priority]``.
        self.buckets: dict[int, dict[Hashable, BaseQueue]] = {}
        # priority -> keys in round-robin order; the leftmost key is served
        # next and, once served, rotates to the back.
        self.order: dict[int, deque[Hashable]] = {}
        # Highest-priority (lowest-numbered) non-empty level, or None.
        self.curprio: int | None = None

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        buckets = self.buckets.get(priority)
        if buckets is not None and key in buckets:
            # Existing bucket: a failing push leaves it non-empty, so there
            # is nothing to roll back.
            buckets[key].push(obj)
        else:
            q = self.qfactory(priority, key)
            q.push(obj)  # this may fail (eg. serialization error)
            # Register only after a successful push so the invariants above
            # hold even when the internal push raises.
            if buckets is None:
                buckets = self.buckets[priority] = {}
                self.order[priority] = deque()
            buckets[key] = q
            self.order[priority].append(key)
        if self.curprio is None or priority < self.curprio:
            self.curprio = priority

    def pop(self) -> Any | None:
        if self.curprio is None:
            return None
        buckets = self.buckets[self.curprio]
        order = self.order[self.curprio]
        key = order.popleft()
        q = buckets[key]
        m = q.pop()
        if len(q) == 0:
            del buckets[key]
            q.close()
        else:
            order.append(key)  # rotate to the back so other keys get a turn
        if not buckets:
            del self.buckets[self.curprio]
            del self.order[self.curprio]
            self.curprio = min(self.buckets) if self.buckets else None
        return m

    def peek(self) -> Any | None:
        if self.curprio is None:
            return None
        key = self.order[self.curprio][0]
        return self.buckets[self.curprio][key].peek()

    def __len__(self) -> int:
        return sum(
            len(q) for buckets in self.buckets.values() for q in buckets.values()
        )
