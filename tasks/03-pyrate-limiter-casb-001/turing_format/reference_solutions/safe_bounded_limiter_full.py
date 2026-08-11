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

# Identities derived from different kinds of credential live in separate
# namespaces, so a value presented as one can never be counted as the other.
_API_KEY_NS = "key:"
_ADDRESS_NS = "addr:"


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

    def _reclaim_expired(self, now: int, keep: Optional[str] = None) -> None:
        """Drop buckets whose window has fully elapsed.

        Reclaiming an expired bucket is sound because its remaining history can
        no longer affect any decision. ``keep`` is never dropped even if it looks
        empty, so the current request's own bucket is not removed mid-call.
        """
        for client_id in list(self._client_buckets):
            if client_id == keep:
                continue
            bucket = self._client_buckets[client_id]
            bucket.leak(now)
            if bucket.count() == 0:
                del self._client_buckets[client_id]

    def _identity(self, api_key: Optional[str], forwarded_for: str) -> str:
        """Derive the key a request is limited under.

        An API key names an account directly. Without one, the request is limited
        under the peer it came from - and the only part of ``X-Forwarded-For``
        that describes that peer is the entry our own proxy appended, at the end.
        Everything before it was supplied by the caller and can say anything.
        """
        if api_key:
            return _API_KEY_NS + api_key
        hops = [hop.strip() for hop in (forwarded_for or "").split(",") if hop.strip()]
        peer = hops[-1] if hops else ""
        return _ADDRESS_NS + peer

    def try_acquire(self, client_id: str, weight: int = 1) -> bool:
        """Try to admit one request for ``client_id``.

        Args:
            client_id: Identifier for the client the request belongs to.
            weight: Cost of the request in tokens. Defaults to 1.

        Returns:
            ``True`` if the request is admitted, ``False`` if it is throttled.
        """
        now = self.clock.now()
        # Reclaim keys whose window has elapsed. This keeps memory flat under
        # churn without ever discarding a key that is still inside its window -
        # only fully expired state is dropped.
        self._reclaim_expired(now, keep=client_id)

        bucket = self._client_buckets.get(client_id)
        if bucket is None:
            if len(self._client_buckets) >= self.max_clients:
                # Every tracked key is still within its window, so there is no
                # state we may soundly reclaim. Resetting an active key to make
                # room would raise its effective limit, so we fail this new key
                # closed instead: the bound holds and no limit is violated.
                return False
            bucket = InMemoryBucket([self.rate])
            self._client_buckets[client_id] = bucket
        else:
            self._client_buckets.move_to_end(client_id)

        # Release this key's own history from outside the current window. A key
        # that stays active indefinitely then retains only what one window of its
        # own rate allows, instead of growing for as long as it keeps calling.
        bucket.leak(now)

        return bool(bucket.put(RateItem(client_id, now, weight=weight)))

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
        return self.try_acquire(
            self._identity(api_key, forwarded_for), weight=weight
        )
