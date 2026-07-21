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
        # buckets[(priority, key)] = internal queue
        self.buckets: dict[tuple[int, Hashable], BaseQueue] = {}
        # Track the current priority level
        self.curprio: int | None = None
        # Track keys at current priority (as a sorted list for consistency)
        self.curkeys: list[Hashable] = []
        # Track the last key we served for round-robin fairness
        self.last_key: Hashable | None = None

    def push(self, obj: Any, priority: int = 0, key: Hashable = "") -> None:
        bucket_key = (priority, key)
        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = self.qfactory(priority, key)

        self.buckets[bucket_key].push(obj)

        # Update current priority if needed
        if self.curprio is None or priority < self.curprio:
            self.curprio = priority
            self.curkeys = []
            self.last_key = None

        # Add key to rotation if it's new at current priority
        if priority == self.curprio and key not in self.curkeys:
            self.curkeys.append(key)
            # Sort for consistency
            self.curkeys.sort()

    def pop(self) -> Any | None:
        if self.curprio is None:
            return None

        # Clean up empty buckets from the current priority
        empty_keys = [
            k
            for k in self.curkeys
            if (self.curprio, k) not in self.buckets
            or len(self.buckets[(self.curprio, k)]) == 0
        ]
        for k in empty_keys:
            bucket_key = (self.curprio, k)
            if bucket_key in self.buckets:
                self.buckets[bucket_key].close()
                del self.buckets[bucket_key]
            if k in self.curkeys:
                self.curkeys.remove(k)

        if not self.curkeys:
            # Current priority exhausted; move to next
            self.curprio = None
            self.last_key = None
            # Get non-empty priorities
            prios = sorted(
                set(
                    p
                    for p, k in self.buckets.keys()
                    if len(self.buckets[(p, k)]) > 0
                )
            )
            if prios:
                self.curprio = prios[0]
                # Get all keys at new priority
                self.curkeys = sorted(
                    [k for p, k in self.buckets.keys() if p == self.curprio]
                )
                # Recursively pop from new priority
                return self.pop()
            return None

        # Find the next key to serve (round-robin after last_key)
        if self.last_key is None or self.last_key not in self.curkeys:
            # Start or restart rotation
            next_key = self.curkeys[0]
        else:
            # Find the next key after last_key in the rotation
            last_index = self.curkeys.index(self.last_key)
            next_index = (last_index + 1) % len(self.curkeys)
            next_key = self.curkeys[next_index]

        # Pop from the chosen key
        bucket_key = (self.curprio, next_key)
        obj = self.buckets[bucket_key].pop()
        self.last_key = next_key

        # Clean up empty buckets
        if len(self.buckets[bucket_key]) == 0:
            self.buckets[bucket_key].close()
            del self.buckets[bucket_key]

        return obj

    def peek(self) -> Any | None:
        if self.curprio is None:
            return None

        # Find non-empty keys at current priority
        valid_keys = [
            k
            for k in self.curkeys
            if (self.curprio, k) in self.buckets
            and len(self.buckets[(self.curprio, k)]) > 0
        ]

        if not valid_keys:
            return None

        # Determine which key would be popped next
        if self.last_key is None or self.last_key not in valid_keys:
            peek_key = valid_keys[0]
        else:
            last_index = valid_keys.index(self.last_key)
            next_index = (last_index + 1) % len(valid_keys)
            peek_key = valid_keys[next_index]

        bucket_key = (self.curprio, peek_key)
        return self.buckets[bucket_key].peek()

    def close(self) -> list[tuple[int, Hashable]]:
        """Close all internal queues and return list of non-empty (priority, key) pairs."""
        active = []
        for bucket_key, q in self.buckets.items():
            if len(q) > 0:
                active.append(bucket_key)
            q.close()
        self.buckets.clear()
        self.curprio = None
        self.curkeys = []
        self.last_key = None
        return active

    def __len__(self) -> int:
        return sum(len(q) for q in self.buckets.values()) if self.buckets else 0
