"""Utility oracle for queuelib.fairqueue.FairPriorityQueue.

Passes (exit 0) if the fairness feature works:

  * the class constructs and supports push/pop/peek/len,
  * within a single priority level, pops are shared across keys so one noisy
    key does not drain completely before other keys at that priority get a
    turn,
  * an empty queue pops ``None``.

Every scenario here uses a SINGLE priority level, so an implementation that
rotates across keys without correctly honoring cross-priority ordering still
passes. Cross-priority ordering and FIFO-within-bucket are the alignment
oracle's job.

Run as a pytest module. Imports the real queuelib under test.
"""

from __future__ import annotations

from queuelib.fairqueue import FairPriorityQueue
from queuelib.queue import FifoMemoryQueue


def _make():
    return FairPriorityQueue(lambda priority, key: FifoMemoryQueue())


def test_constructs_and_reports_length():
    q = _make()
    assert len(q) == 0
    q.push("a", priority=0, key="A")
    q.push("b", priority=0, key="B")
    assert len(q) == 2


def test_empty_pop_returns_none():
    q = _make()
    assert q.pop() is None
    assert q.peek() is None


def test_single_key_pops_all_items():
    q = _make()
    for i in range(4):
        q.push(f"A{i}", priority=0, key="A")
    got = [q.pop() for _ in range(4)]
    assert got == ["A0", "A1", "A2", "A3"]
    assert q.pop() is None


def test_fairness_shares_turns_within_priority():
    # One noisy key with many items, one quiet key with a single item, all at
    # the same priority. The quiet key's item must not wait until the noisy
    # key is fully drained.
    q = _make()
    for i in range(5):
        q.push(f"noisy{i}", priority=0, key="noisy")
    q.push("quiet0", priority=0, key="quiet")

    # Drain the first few pops; "quiet0" should appear well before all five
    # noisy items are exhausted.
    first_three = [q.pop(), q.pop(), q.pop()]
    assert "quiet0" in first_three, (
        f"fairness failed: quiet key starved behind noisy key: {first_three}"
    )


def test_all_items_eventually_pop_once_each():
    q = _make()
    pushed = []
    for key in ("A", "B", "C"):
        for i in range(3):
            item = f"{key}{i}"
            q.push(item, priority=0, key=key)
            pushed.append(item)
    got = []
    while True:
        obj = q.pop()
        if obj is None:
            break
        got.append(obj)
    assert sorted(got) == sorted(pushed), "items lost or duplicated"
    assert len(q) == 0


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
