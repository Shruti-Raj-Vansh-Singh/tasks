"""Utility oracle for persistqueue.redelivery.RedeliveryAckQueue.

Passes (exit 0) if the redelivery / dead-letter feature works within a
single process:

  * the class constructs and delivers items,
  * an item nack-ed more than max_attempts times is dead-lettered instead of
    being redelivered again,
  * an item acked normally is never dead-lettered,
  * `dead_letter_ids()` / `attempts()` report the feature state.

Every scenario here runs inside ONE queue instance (no crash/restart), so an
implementation that tracks attempts only in memory still passes. Whether the
attempt count survives a process restart is the alignment oracle's job.

Run as a pytest module. Imports the real persistqueue under test.
"""

from __future__ import annotations

import tempfile

from persistqueue.redelivery import RedeliveryAckQueue


def _queue(max_attempts):
    return RedeliveryAckQueue(tempfile.mkdtemp(), max_attempts=max_attempts)


def test_constructs_and_delivers():
    q = _queue(3)
    q.put("a")
    raw = q.get(raw=True, block=False)
    assert raw["data"] == "a"
    assert "pqid" in raw


def test_nack_redelivers_while_attempts_remain():
    q = _queue(max_attempts=3)
    q.put("job")
    seen = 0
    for _ in range(3):
        raw = q.get(raw=True, block=False)
        seen += 1
        q.nack(id=raw["pqid"])
    # Still under the limit at this point -> not yet dead-lettered.
    assert q.dead_letter_ids() == [], (
        f"item dead-lettered too early: {q.dead_letter_ids()}"
    )
    assert seen == 3


def test_poison_message_is_dead_lettered_single_process():
    q = _queue(max_attempts=2)
    pqid = q.put("poison")
    # Deliver + nack repeatedly; after attempts exceed max_attempts it must
    # be dead-lettered rather than delivered again.
    for _ in range(10):
        try:
            raw = q.get(raw=True, block=False)
        except Exception:
            break
        q.nack(id=raw["pqid"])
    assert q.dead_letter_ids() == [pqid], (
        f"poison message not dead-lettered: dead={q.dead_letter_ids()}"
    )


def test_acked_item_is_never_dead_lettered():
    q = _queue(max_attempts=1)
    q.put("ok")
    raw = q.get(raw=True, block=False)
    q.ack(id=raw["pqid"])
    assert q.dead_letter_ids() == [], "a normally-acked item was dead-lettered"


def test_attempts_increments_on_delivery():
    q = _queue(max_attempts=5)
    pqid = q.put("x")
    q.get(raw=True, block=False)
    assert q.attempts(pqid) == 1
    q.nack(id=pqid)
    q.get(raw=True, block=False)
    assert q.attempts(pqid) == 2


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
