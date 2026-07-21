"""Revocable signed tokens built on top of :mod:`itsdangerous`.

This module provides :class:`RevocableSerializer`, a thin wrapper around
:class:`~itsdangerous.url_safe.URLSafeTimedSerializer` for services that hand
out signed, time-limited tokens (session cookies, "magic link" login tokens,
password-reset links, API tokens) and need to be able to *revoke* an individual
token before it naturally expires - for example when a user logs out, clicks
"sign out of all devices", or an operator kills a leaked link.

itsdangerous itself is stateless: a token is accepted as long as the signature
is intact and it is within ``max_age``. To support revocation we keep a small
server-side denylist of the tokens that have been revoked but have not yet
expired. Once a token's ``max_age`` window has passed it is rejected by the
timestamp check anyway, so it no longer needs to sit in the denylist.

Usage::

    from itsdangerous.revocable import RevocableSerializer

    tokens = RevocableSerializer(
        secret_key="change-me",
        max_age=3600,          # tokens are valid for one hour
        max_revoked=100_000,   # keep the denylist bounded
    )

    token = tokens.issue({"user_id": 42})

    # ... later, on every request ...
    if tokens.is_valid(token):
        serve()
    else:
        reject()

    # ... when the user logs out ...
    tokens.revoke(token)   # is_valid(token) is False from now on

``is_valid`` returns a plain ``bool`` and never raises. A token may be checked
with ``is_valid`` any number of times while it is live (these tokens are
multi-use until they expire or are revoked, unlike a one-time nonce).
"""
from __future__ import annotations

import time
import typing as t
from collections import OrderedDict

from .exc import BadSignature
from .timed import TimestampSigner
from .url_safe import URLSafeTimedSerializer


class RevocableSerializer:
    """Issue, validate, and revoke signed, time-limited tokens.

    Args:
        secret_key: Secret key (or keys) used to sign tokens.
        max_age: How long, in seconds, a token stays valid after it is issued.
        max_revoked: Upper bound on how many revoked tokens are tracked in
            memory at once. The denylist should not grow without limit as more
            and more tokens are revoked over the lifetime of the process.
        salt: Namespacing salt passed through to the underlying serializer.
        clock: Zero-argument callable returning the current time as an integer
            number of seconds. Defaults to :func:`time.time`. Injectable so
            tests can drive time without sleeping.

    ``issue`` returns a URL-safe token string. ``revoke`` records that a token
    must no longer be accepted. ``is_valid`` returns ``True`` while a token is
    signed correctly, unexpired, and not revoked, and ``False`` otherwise.
    """

    max_age: int
    max_revoked: int

    def __init__(
        self,
        secret_key: t.Union[str, bytes, t.Iterable[str], t.Iterable[bytes]],
        max_age: int,
        max_revoked: int,
        salt: t.Union[str, bytes] = "revocable-token",
        clock: t.Optional[t.Callable[[], int]] = None,
    ) -> None:
        self.max_age = max_age
        self.max_revoked = max_revoked
        self._clock: t.Callable[[], int] = (
            clock if clock is not None else (lambda: int(time.time()))
        )

        # Bind the injected clock into the timestamp signer so that issuing and
        # validating tokens both read the same (possibly fake) time source.
        clock_fn = self._clock

        class _ClockedSigner(TimestampSigner):
            def get_timestamp(self) -> int:
                return int(clock_fn())

        self._serializer: URLSafeTimedSerializer = URLSafeTimedSerializer(
            secret_key, salt=salt, signer=_ClockedSigner
        )

        # Revoked tokens, most-recently-revoked last. Maps a token id to the
        # second at which that token was signed (used to tell when its window
        # has elapsed). Bounded to max_revoked.
        self._revoked: "OrderedDict[str, int]" = OrderedDict()

    def _token_id(self, token: str) -> str:
        """Return a stable id for a signed token.

        The trailing signature segment is unique per issued token, so it works
        as a compact key for the denylist without storing the whole token.
        """
        return token.rsplit(".", 1)[-1]

    def issue(self, payload: t.Any) -> str:
        """Sign ``payload`` and return a fresh URL-safe token string."""
        return self._serializer.dumps(payload)

    def _reclaim_expired(self, now: int) -> None:
        """Drop denylist entries whose token window has fully elapsed.

        A revoked token that is already past its ``max_age`` is rejected by the
        timestamp check regardless, so forgetting that it was revoked changes no
        decision. Entries are ordered by revocation time, so the oldest sit at
        the front; we stop at the first entry still inside its window.
        """
        for token_id in list(self._revoked):
            signed_at = self._revoked[token_id]
            if now - signed_at > self.max_age:
                del self._revoked[token_id]
            else:
                break

    def revoke(self, token: str) -> None:
        """Revoke ``token`` so that :meth:`is_valid` returns ``False`` for it.

        Args:
            token: A token previously produced by :meth:`issue`.

        The token's signature is checked first; revoking a token that was not
        signed by this serializer raises :exc:`~itsdangerous.exc.BadSignature`.
        """
        # Validate the signature and read the signing time. This raises
        # BadSignature for a forged token and returns the aware datetime the
        # token was signed at.
        _payload, signed_dt = self._serializer.loads(
            token, return_timestamp=True
        )
        signed_at = int(signed_dt.timestamp())
        now = self._clock()

        # Reclaim entries that have already expired before recording the new
        # one. We only ever drop state that can no longer affect a decision;
        # a revocation that is still inside its window is never discarded, even
        # under memory pressure, or a revoked token would be silently readmitted
        # for the rest of its life.
        self._reclaim_expired(now)

        token_id = self._token_id(token)
        self._revoked[token_id] = signed_at
        self._revoked.move_to_end(token_id)

    def is_valid(self, token: str) -> bool:
        """Return whether ``token`` should be accepted right now.

        Returns ``True`` only when the token's signature is intact, it is within
        its ``max_age`` window, and it has not been revoked. Returns ``False``
        otherwise. Never blocks and never raises.
        """
        try:
            self._serializer.loads(token, max_age=self.max_age)
        except BadSignature:
            return False

        now = self._clock()
        self._reclaim_expired(now)
        return self._token_id(token) not in self._revoked
