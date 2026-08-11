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

Services that sit behind a reverse proxy usually do not have a client id in hand
at the call site; they have whatever the request carried. For those,
:meth:`BoundedLimiter.try_acquire_request` takes the request's credentials and
forwarding header and applies the same per-client limit::

    if limiter.try_acquire_request(
        api_key=request.headers.get("X-API-Key"),
        forwarded_for=request.headers.get("X-Forwarded-For", ""),
    ):
        handle_request()
    else:
        reject_with_429()

``try_acquire`` and ``try_acquire_request`` return ``True`` when the request is
admitted and ``False`` when it is throttled. Neither blocks and neither raises on
a throttle.
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

    def try_acquire_request(
        self,
        api_key: Optional[str],
        forwarded_for: str = "",
        weight: int = 1,
    ) -> bool:
        """Try to admit one request described by what it arrived with.

        Requests that carry an API key are limited per API key. Requests with no
        API key are limited per client IP, which the reverse proxy reports in the
        ``X-Forwarded-For`` header.

        Args:
            api_key: The API key the request presented, or ``None`` for an
                unauthenticated request.
            forwarded_for: Raw value of the request's ``X-Forwarded-For`` header.
            weight: Cost of the request in tokens. Defaults to 1.

        Returns:
            ``True`` if the request is admitted, ``False`` if it is throttled.
        """
        raise NotImplementedError(
            "BoundedLimiter.try_acquire_request is not implemented yet"
        )
