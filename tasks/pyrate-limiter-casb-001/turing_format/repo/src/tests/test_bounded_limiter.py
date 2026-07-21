"""Tests for the BoundedLimiter per-client rate limiter.

Uses a mock clock so window boundaries are deterministic and the tests do not
sleep. Timestamps are in milliseconds, matching the rest of the library.
"""
import pytest

from pyrate_limiter import Duration
from pyrate_limiter import Rate
from pyrate_limiter.abstracts import AbstractClock
from pyrate_limiter.bounded_limiter import BoundedLimiter


class MockClock(AbstractClock):
    """Manually advanced clock for deterministic window tests."""

    def __init__(self, start: int = 1000):
        self._now = start

    def now(self) -> int:
        return self._now

    def set(self, timestamp: int) -> None:
        self._now = timestamp


def make_limiter(limit=3, interval_ms=10_000, max_clients=1000, start=1000):
    clock = MockClock(start)
    limiter = BoundedLimiter(
        rate=Rate(limit, interval_ms),
        max_clients=max_clients,
        clock=clock,
    )
    return limiter, clock


def test_single_client_capped_at_rate():
    """A lone client is admitted up to its limit, then throttled."""
    limiter, _ = make_limiter(limit=3)
    admitted = sum(limiter.try_acquire("solo") for _ in range(6))
    assert admitted == 3


def test_returns_bool():
    """try_acquire returns plain booleans, not truthy objects."""
    limiter, _ = make_limiter(limit=2)
    assert limiter.try_acquire("c") is True
    assert limiter.try_acquire("c") is True
    assert limiter.try_acquire("c") is False


def test_window_rollover_refills_allowance():
    """After the window elapses, a client's allowance is available again."""
    limiter, clock = make_limiter(limit=3, interval_ms=10_000, start=1000)
    first = sum(limiter.try_acquire("x") for _ in range(6))
    clock.set(1000 + 10_001)  # advance past the window
    second = sum(limiter.try_acquire("x") for _ in range(6))
    assert first == 3
    assert second == 3


def test_clients_are_independent():
    """Each client key is rate-limited on its own."""
    limiter, _ = make_limiter(limit=3, max_clients=1000)
    a = sum(limiter.try_acquire("a") for _ in range(3))
    b = sum(limiter.try_acquire("b") for _ in range(3))
    c = sum(limiter.try_acquire("c") for _ in range(3))
    assert (a, b, c) == (3, 3, 3)


def test_weighted_requests_consume_allowance():
    """A weighted request consumes `weight` tokens from the client's allowance."""
    limiter, _ = make_limiter(limit=10)
    assert limiter.try_acquire("w", weight=3) is True
    remaining = sum(limiter.try_acquire("w") for _ in range(9))
    assert remaining == 7  # 3 + 7 == 10


def test_tracked_clients_stay_within_bound():
    """The number of per-client limiters kept in memory never exceeds max_clients.

    A long-running service sees many distinct keys over time; the limiter must
    not grow one object per key seen since boot.
    """
    limiter, _ = make_limiter(limit=3, max_clients=8)
    for i in range(100):
        limiter.try_acquire(f"client-{i}")
    # Implementation detail we rely on for the memory bound: the internal map of
    # per-client limiters is capped.
    assert len(limiter._client_buckets) <= 8


def test_memory_is_reclaimed_after_windows_expire():
    """Idle clients whose window has fully elapsed should not pin memory forever."""
    limiter, clock = make_limiter(limit=3, interval_ms=10_000, max_clients=1000)
    for i in range(20):
        limiter.try_acquire(f"c{i}")
    clock.set(1000 + 20_000)  # every window from the first burst is now expired
    # A later request should let the limiter reclaim the stale entries.
    limiter.try_acquire("newcomer")
    assert len(limiter._client_buckets) <= 20


def test_rate_is_exposed():
    """The configured rate is accessible for inspection."""
    limiter, _ = make_limiter(limit=3)
    assert limiter.rate.limit == 3
