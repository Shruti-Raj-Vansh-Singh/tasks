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
        self.queues: dict[tuple[int, Hashable], BaseQueue] = {}
        self.curprio: int | None = None
        self.last_key_per_prio: dict[int, Hashable | None] = {}

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        bucket = (priority, key)
        if bucket not in self.queues:
            self.queues[bucket] = self.qfactory(priority, key)
        q = self.queues[bucket]
        q.push(obj)
        if self.curprio is None or priority < self.curprio:
            self.curprio = priority

    def pop(self) -> Any | None:
        if self.curprio is None:
            return None

        keys_at_priority = sorted([
            k for p, k in self.queues.keys() if p == self.curprio and len(self.queues[(p, k)]) > 0
        ])

        if not keys_at_priority:
            self._advance_priority()
            return self.pop()

        last_key = self.last_key_per_prio.get(self.curprio)
        if last_key is None or last_key not in keys_at_priority:
            next_key = keys_at_priority[0]
        else:
            idx = keys_at_priority.index(last_key)
            next_key = keys_at_priority[(idx + 1) % len(keys_at_priority)]

        self.last_key_per_prio[self.curprio] = next_key
        q = self.queues[(self.curprio, next_key)]
        obj = q.pop()

        if len(q) == 0:
            del self.queues[(self.curprio, next_key)]
            q.close()
            if not any(p == self.curprio for p, _ in self.queues.keys()):
                self._advance_priority()

        return obj

    def peek(self) -> Any | None:
        if self.curprio is None:
            return None

        keys_at_priority = sorted([
            k for p, k in self.queues.keys() if p == self.curprio and len(self.queues[(p, k)]) > 0
        ])

        if not keys_at_priority:
            return None

        last_key = self.last_key_per_prio.get(self.curprio)
        if last_key is None or last_key not in keys_at_priority:
            next_key = keys_at_priority[0]
        else:
            idx = keys_at_priority.index(last_key)
            next_key = keys_at_priority[(idx + 1) % len(keys_at_priority)]

        q = self.queues[(self.curprio, next_key)]
        return q.peek()

    def __len__(self) -> int:
        return sum(len(q) for q in self.queues.values()) if self.queues else 0

    def _advance_priority(self) -> None:
        prios = sorted(set(p for p, _ in self.queues.keys() if len(self.queues[(p, _)]) > 0))
        self.curprio = min(prios) if prios else None
