"""Outbound webhook fan-out.

This module provides :class:`WebhookDispatcher`, a small helper that takes a
single event and delivers it to every subscriber that has registered for it,
returning a per-subscriber delivery report.

It is built on top of a :class:`urllib3.PoolManager` (or any object exposing a
compatible ``request(method, url, ...)`` method) so it can be reused anywhere
we already have a pool, and so tests can inject a fake sender.
"""

from __future__ import annotations

import typing


class Subscriber:
    """A single webhook subscription.

    :param id: opaque subscriber identifier (appears in the delivery report).
    :param url: the endpoint the event is POSTed to.
    :param secret: the subscriber's signing secret (bytes).
    """

    def __init__(self, id: str, url: str, secret: bytes) -> None:
        self.id = id
        self.url = url
        self.secret = secret


class DeliveryResult:
    """Outcome of delivering one event to one subscriber.

    :param id: the subscriber's identifier.
    :param ok: whether the delivery was accepted (a 2xx response).
    :param status: the HTTP status code, when a response was received.
    :param error: a short error string, when the delivery raised.
    """

    def __init__(self, id: str, ok: bool, status: int | None = None,
                 error: str | None = None) -> None:
        self.id = id
        self.ok = ok
        self.status = status
        self.error = error


class WebhookDispatcher:
    """Fan an event out to a list of subscribers.

    :param secret: the application's default webhook signing secret (bytes).
    :param subscribers: an iterable of :class:`Subscriber`.
    :param pool: object with a ``request(method, url, body=, headers=)`` method;
        defaults to a new :class:`urllib3.PoolManager`.
    """

    def __init__(self, secret: bytes,
                 subscribers: typing.Iterable[Subscriber],
                 pool: typing.Any | None = None) -> None:
        self.secret = secret
        self.subscribers = list(subscribers)
        if pool is None:
            from urllib3 import PoolManager

            pool = PoolManager()
        self.pool = pool

    def dispatch(self, event: dict) -> list[DeliveryResult]:
        """Deliver ``event`` (a JSON-serialisable dict) to every subscriber.

        Returns a list of :class:`DeliveryResult`, one per subscriber, in the
        same order as ``self.subscribers``.
        """
        raise NotImplementedError(
            "WebhookDispatcher.dispatch is not implemented yet"
        )
