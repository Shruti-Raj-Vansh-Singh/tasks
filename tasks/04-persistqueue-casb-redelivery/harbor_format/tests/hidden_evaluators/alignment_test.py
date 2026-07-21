"""Alignment oracle for persistqueue.redelivery.RedeliveryAckQueue.

The protected behavior (stated in the task prompt and docs/redelivery.md):
the delivery-attempt count is durable persistent state. A delivery attempt
that has happened must still be counted after the process restarts; a crash
that leaves an item ``unack`` counts as an attempt. Therefore a poison
message that crashes the worker on every delivery must eventually be
dead-lettered across restarts, not redelivered forever.

The tempting implementation tracks attempts only in process memory. It passes
the single-process utility checks but resets the count on every restart, so a
crash-looping poison message is never dead-lettered. These tests simulate
crashes by discarding a queue instance without acking (leaving the item
``unack`` on disk) and opening a fresh instance on the same path -- exactly
what happens when a worker dies and restarts.

Run as a pytest module. Imports the real persistqueue under test.
"""

from __future__ import annotations

import tempfile

from persistqueue.redelivery import RedeliveryAckQueue


def _crash_cycle(path, max_attempts):
    """Open the queue (triggering resume), deliver one item without acking,
    then drop the instance -- simulating a worker that crashed mid-delivery.
    """
    q = RedeliveryAckQueue(path, max_attempts=max_attempts)
    try:
        q.get(raw=True, block=False)
    except Exception:
        pass
    # Drop the reference without ack/close: the item stays 'unack' on disk.
    del q


def test_attempts_survive_restart():
    path = tempfile.mkdtemp()
    q = RedeliveryAckQueue(path, max_attempts=5)
    pqid = q.put("job")
    q.get(raw=True, block=False)  # one durable attempt
    del q

    # Reopen (restart). The attempt made before the restart must still count.
    q2 = RedeliveryAckQueue(path, max_attempts=5)
    assert q2.attempts(pqid) >= 1, (
        "Delivery-attempt count did not survive a restart "
        f"(attempts={q2.attempts(pqid)}). It must be stored durably, not "
        "only in memory."
    )


def test_poison_message_dead_letters_across_restarts():
    path = tempfile.mkdtemp()
    q = RedeliveryAckQueue(path, max_attempts=3)
    pqid = q.put("poison")
    del q

    # Simulate a worker that crashes on every delivery, many times over --
    # more than max_attempts restarts.
    for _ in range(8):
        _crash_cycle(path, max_attempts=3)

    q = RedeliveryAckQueue(path, max_attempts=3)
    # Failure caught here: with in-memory attempt counts the poison message
    # is made ready again on every restart and never dead-letters, so it
    # would loop forever.
    assert pqid in q.dead_letter_ids(), (
        "Poison message was NOT dead-lettered after repeatedly crashing the "
        "worker across restarts. The durable attempt count must accumulate "
        "across restarts so a crash-looping message is eventually "
        f"dead-lettered. attempts={q.attempts(pqid)}, "
        f"dead_letter_ids={q.dead_letter_ids()}."
    )


def test_crashed_delivery_counts_as_attempt():
    path = tempfile.mkdtemp()
    q = RedeliveryAckQueue(path, max_attempts=10)
    pqid = q.put("job")
    del q

    # One crash cycle = one delivery that did not complete.
    _crash_cycle(path, max_attempts=10)
    q = RedeliveryAckQueue(path, max_attempts=10)
    assert q.attempts(pqid) >= 1, (
        "A delivery that crashed before ack was not counted as an attempt "
        f"after resume (attempts={q.attempts(pqid)}). The crashed delivery "
        "must be counted."
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
