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
        # Structure: {priority: {key: queue}}
        self.priorities: dict[int, dict[Hashable, BaseQueue]] = {}
        # Track the next key to serve for each priority (for round-robin fairness)
        self.key_rotation: dict[int, list[Hashable]] = {}
        # Current priority level (cached for efficiency)
        self.curprio: int | None = None

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        # Initialize priority level if needed
        if priority not in self.priorities:
            self.priorities[priority] = {}
            self.key_rotation[priority] = []

        # Initialize key's queue if needed
        if key not in self.priorities[priority]:
            self.priorities[priority][key] = self.qfactory(priority, key)
            self.key_rotation[priority].append(key)

        # Push to the appropriate bucket
        self.priorities[priority][key].push(obj)

        # Update current priority if this is higher (lower number)
        if self.curprio is None or priority < self.curprio:
            self.curprio = priority

    def pop(self) -> Any | None:
        if self.curprio is None:
            return None

        # Get the keys at the current priority level
        keys_dict = self.priorities[self.curprio]
        if not keys_dict:
            return None

        # Find the first key with items (skip empty ones)
        rotation = self.key_rotation[self.curprio]
        item = None
        next_key_idx = 0

        for i, key in enumerate(rotation):
            if key in keys_dict and len(keys_dict[key]) > 0:
                item = keys_dict[key].pop()
                # Move this key to the end of the rotation for next time
                rotation.pop(i)
                rotation.append(key)
                break

        # Clean up empty queues and priority levels
        for key in list(keys_dict.keys()):
            if len(keys_dict[key]) == 0:
                keys_dict[key].close()
                del keys_dict[key]
                if key in rotation:
                    rotation.remove(key)

        # If current priority is now empty, find the next one
        if len(keys_dict) == 0:
            del self.priorities[self.curprio]
            del self.key_rotation[self.curprio]
            # Find next highest priority
            if self.priorities:
                self.curprio = min(self.priorities.keys())
            else:
                self.curprio = None

        return item

    def peek(self) -> Any | None:
        if self.curprio is None:
            return None

        # Get the keys at the current priority level
        keys_dict = self.priorities[self.curprio]
        if not keys_dict:
            return None

        # Find the first key with items
        rotation = self.key_rotation[self.curprio]
        for key in rotation:
            if key in keys_dict and len(keys_dict[key]) > 0:
                return keys_dict[key].peek()

        return None

    def __len__(self) -> int:
        total = 0
        for priority_dict in self.priorities.values():
            for queue in priority_dict.values():
                total += len(queue)
        return total
