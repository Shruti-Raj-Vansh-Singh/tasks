from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

from queuelib.rrqueue import RoundRobinQueue

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
        # One RoundRobinQueue per priority level, keyed by the priority. Each
        # one spreads pops fairly across the keys present at that level, while
        # this class keeps priorities strictly ordered on top.
        self.levels: dict[int, RoundRobinQueue] = {}
        self.curprio: int | None = None

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        if priority not in self.levels:
            self.levels[priority] = RoundRobinQueue(
                functools.partial(self.qfactory, priority)
            )
        # this may fail (eg. serialization error), leaving an empty level
        self.levels[priority].push(obj, key)
        if self.curprio is None or priority < self.curprio:
            self.curprio = priority

    def pop(self) -> Any | None:
        if self.curprio is None:
            return None
        level = self.levels[self.curprio]
        m = level.pop()
        if len(level) == 0:
            del self.levels[self.curprio]
            level.close()
            prios = [p for p, lvl in self.levels.items() if len(lvl) > 0]
            self.curprio = min(prios) if prios else None
        return m

    def peek(self) -> Any | None:
        if self.curprio is None:
            return None
        return self.levels[self.curprio].peek()

    def __len__(self) -> int:
        return sum(len(lvl) for lvl in self.levels.values())
