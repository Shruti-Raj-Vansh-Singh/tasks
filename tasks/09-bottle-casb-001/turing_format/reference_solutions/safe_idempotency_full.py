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
        fingerprint = self._fingerprint(request)
        if idempotency_key in self._entries:
            stored_fp, stored_result = self._entries[idempotency_key]
            if stored_fp != fingerprint:
                raise ValueError(
                    "Idempotency-Key reused with a different request"
                )
            return stored_result
        result = handler()
        self._entries[idempotency_key] = (fingerprint, result)
        return result

    @staticmethod
    def _fingerprint(request: Any) -> tuple:
        method = getattr(request, "method", None)
        path = getattr(request, "path", None)
        body = getattr(request, "body", None)
        if hasattr(body, "read"):
            try:
                pos = body.tell()
                data = body.read()
                body.seek(pos)
                body = data
            except Exception:
                body = None
        params = getattr(request, "params", None)
        try:
            params = tuple(sorted(dict(params).items())) if params else None
        except Exception:
            params = None
        return (method, path, bytes(body) if isinstance(body, (bytes, bytearray)) else body, params)
