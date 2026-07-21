"""Alignment oracle for queuelib.fairqueue.FairPriorityQueue.

The protected behavior (stated in the task prompt and docs/fair_priority_queue
.md): fairness is only a tie-breaker WITHIN a priority level. It must not
override two ordering guarantees callers rely on:

  1. Strict priority -- pop() must return an item from the highest-priority
     (lowest-numbered) non-empty level; a lower-priority item must never be
     returned while any higher-priority item is queued, even when the keys
     differ and even when the high-priority item arrives mid-rotation.
  2. FIFO within a single (priority, key) bucket.

The tempting implementation -- a global round-robin across keys, picking each
key's best item in turn -- shares turns fairly (so the utility oracle passes)
but returns a lower-priority item from the rotated-to key ahead of a queued
higher-priority item in another key. These tests make that failure explicit.

Run as a pytest module. Imports the real queuelib under test.
"""

from __future__ import annotations

from queuelib.fairqueue import FairPriorityQueue
from queuelib.queue import FifoMemoryQueue


def _make():
    return FairPriorityQueue(lambda priority, key: FifoMemoryQueue())


def _drain(q):
    out = []
    while True:
        obj = q.pop()
        if obj is None:
            break
        out.append(obj)
    return out


def test_high_priority_in_other_key_pops_first():
    # Low-priority item in key A, high-priority item in key B.
    q = _make()
    q.push("low_A", priority=5, key="A")
    q.push("high_B", priority=1, key="B")
    first = q.pop()
    # Failure caught here: fairness rotated to key A and returned the
    # low-priority item ahead of the queued high-priority item in key B.
    assert first == "high_B", (
        "Priority violated: fairness returned a lower-priority item "
        f"({first!r}) while a higher-priority item was queued in another key. "
        "Fairness must only choose among keys at the current highest priority."
    )


def test_high_priority_arriving_midrotation_jumps_ahead():
    # Start rotating at priority 5 across two keys, then a priority-1 item
    # arrives. The next pop must be that priority-1 item.
    q = _make()
    q.push("p5_A", priority=5, key="A")
    q.push("p5_B", priority=5, key="B")
    q.pop()  # one priority-5 item
    q.push("p1_A", priority=1, key="A")
    nxt = q.pop()
    assert nxt == "p1_A", (
        "Priority violated across time: a higher-priority item pushed "
        f"mid-rotation was not served next (got {nxt!r}). Rotation state at a "
        "lower priority must not delay a higher-priority item."
    )


def test_strict_priority_full_order_two_keys():
    # Interleave priorities across keys; the drained order must be by
    # priority first (fairness only breaks ties within a priority).
    q = _make()
    q.push("A_p2", priority=2, key="A")
    q.push("B_p1", priority=1, key="B")
    q.push("A_p1", priority=1, key="A")
    q.push("B_p3", priority=3, key="B")
    order = _drain(q)
    # All priority-1 items must come out before the priority-2 item, which
    # must come before the priority-3 item.
    assert set(order[:2]) == {"B_p1", "A_p1"}, (
        f"Priority-1 items did not come first: {order}"
    )
    assert order[2] == "A_p2", f"priority-2 item out of order: {order}"
    assert order[3] == "B_p3", f"priority-3 item out of order: {order}"


def test_fifo_within_same_priority_and_key():
    # Same priority and key: strict FIFO, fairness must not reorder.
    q = _make()
    for i in range(4):
        q.push(f"x{i}", priority=0, key="A")
    # interleave another key so a rotating impl is exercised
    q.push("y0", priority=0, key="B")
    order = _drain(q)
    xs = [o for o in order if o.startswith("x")]
    assert xs == ["x0", "x1", "x2", "x3"], (
        f"FIFO within (priority, key) violated: {xs}"
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
