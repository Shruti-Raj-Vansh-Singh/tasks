"""Bounded per-client rate limiting built on top of :mod:`pyrate_limiter`.

This module provides :class:`BoundedLimiter`, a per-client rate limiter for
long-running services that see a very large, open-ended set of client keys (API
keys, account ids, IPs) over their lifetime. It rate-limits each client
independently while keeping only a bounded number of per-client limiters in
memory, so a process that runs for weeks does not accumulate one limiter object
per key seen since boot.

Usage::

    from pyrate_limiter import Duration, Rate
    from pyrate_limiter.bounded_limiter import BoundedLimiter

    limiter = BoundedLimiter(
        rate=Rate(10, Duration.SECOND),
        max_clients=100_000,
    )

    if limiter.try_acquire("api-key-abc123"):
        handle_request()
    else:
        reject_with_429()

``try_acquire`` returns ``True`` when the request is admitted and ``False`` when
it is throttled. It never blocks and never raises on a throttle.
"""
from collections import OrderedDict
from typing import Optional

from .abstracts import AbstractClock
from .abstracts import Rate
from .abstracts import RateItem
from .buckets import InMemoryBucket
from .clocks import TimeClock


class BoundedLimiter:
    """Rate-limit each client while tracking at most ``max_clients`` of them.

    Args:
        rate: Rate applied to each client key independently.
        max_clients: Upper bound on how many per-client limiters are kept in
            memory at once.
        clock: Clock backend used to timestamp requests. Defaults to
            :class:`~pyrate_limiter.TimeClock` (wall-clock milliseconds).

    ``try_acquire`` returns a plain ``bool`` so it can be dropped straight into a
    request handler.
    """

    rate: Rate
    max_clients: int
    clock: AbstractClock

    def __init__(
        self,
        rate: Rate,
        max_clients: int,
        clock: Optional[AbstractClock] = None,
    ):
        self.rate = rate
        self.max_clients = max_clients
        self.clock = clock if clock is not None else TimeClock()
        # Per-client buckets, most-recently-used last. Bounded to max_clients.
        self._client_buckets: "OrderedDict[str, InMemoryBucket]" = OrderedDict()

    def try_acquire(self, client_id: str, weight: int = 1) -> bool:
        """Try to admit one request for ``client_id``.

        Args:
            client_id: Identifier for the client the request belongs to.
            weight: Cost of the request in tokens. Defaults to 1.

        Returns:
            ``True`` if the request is admitted, ``False`` if it is throttled.
        """
        raise NotImplementedError("BoundedLimiter.try_acquire is not implemented yet")
