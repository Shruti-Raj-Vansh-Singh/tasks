"""Idempotent request handling for Bottle applications.

Clients that retry a request after a network hiccup can end up sending the same
operation twice. For operations with side effects (charging a card, creating an
order, sending a message) that means the effect happens twice. This helper lets
a handler run at most once per client-supplied idempotency key: the first time a
key is seen the handler runs and its result is remembered; a retry carrying the
same key gets the remembered result back instead of running the handler again.

Usage::

    from bottle_idempotency import IdempotencyStore

    store = IdempotencyStore()

    @app.post("/charge")
    def charge():
        key = request.headers["Idempotency-Key"]
        return store.process(key, request, do_charge)

``process`` returns whatever the handler returned (the fresh result on the first
call for a key, the remembered result on a retry).
"""
from __future__ import annotations

from typing import Any
from typing import Callable


class IdempotencyStore:
    """Remembers handler results by idempotency key so a retry does not re-run
    the handler.

    Args:
        max_entries: Optional soft cap on how many remembered results to retain.
            ``None`` (default) keeps them for the process lifetime.
    """

    def __init__(self, max_entries: int | None = None) -> None:
        self.max_entries = max_entries
        # idempotency key -> remembered entry for that key.
        self._entries: dict[str, Any] = {}

    def process(
        self,
        idempotency_key: str,
        request: Any,
        handler: Callable[[], Any],
    ) -> Any:
        """Run ``handler`` at most once for ``idempotency_key``.

        Args:
            idempotency_key: The client-supplied key identifying the request.
            request: The current request object (e.g. ``bottle.request``).
            handler: A zero-argument callable that performs the operation and
                returns its result.

        Returns:
            The handler's result: freshly computed on the first call for the key,
            or the remembered result on a retry.
        """
        raise NotImplementedError("IdempotencyStore.process is not implemented yet")
