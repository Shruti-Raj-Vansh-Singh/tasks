"""Tests for :class:`itsdangerous.revocable.RevocableSerializer`.

These use a small mock clock so token lifetimes can be driven without sleeping;
timestamps are integer seconds. Copy the ``Clock`` pattern below for new tests.
"""
from __future__ import annotations

import pytest

from itsdangerous.exc import BadSignature
from itsdangerous.revocable import RevocableSerializer


class Clock:
    """A fake clock: ``clock()`` returns the current second; ``set`` moves it."""

    def __init__(self, start: int = 1_000_000) -> None:
        self._now = start

    def __call__(self) -> int:
        return self._now

    def set(self, now: int) -> None:
        self._now = now

    def tick(self, seconds: int = 1) -> None:
        self._now += seconds


def make(max_age: int = 100, max_revoked: int = 1000, clock: Clock | None = None):
    clock = clock if clock is not None else Clock()
    return (
        RevocableSerializer(
            secret_key="test-secret",
            max_age=max_age,
            max_revoked=max_revoked,
            clock=clock,
        ),
        clock,
    )


def test_issue_and_validate():
    s, _ = make()
    token = s.issue({"user_id": 7})
    assert s.is_valid(token) is True


def test_revoke_makes_token_invalid():
    s, _ = make()
    token = s.issue({"user_id": 7})
    assert s.is_valid(token) is True
    s.revoke(token)
    assert s.is_valid(token) is False


def test_unrevoked_token_stays_valid():
    s, _ = make()
    a = s.issue("a")
    b = s.issue("b")
    s.revoke(a)
    # Revoking one token does not affect another.
    assert s.is_valid(a) is False
    assert s.is_valid(b) is True


def test_expired_token_is_invalid():
    s, clock = make(max_age=100)
    token = s.issue("x")
    assert s.is_valid(token) is True
    clock.set(clock() + 101)
    assert s.is_valid(token) is False


def test_tampered_token_is_invalid():
    s, _ = make()
    token = s.issue("x")
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    assert s.is_valid(tampered) is False


def test_revoke_rejects_foreign_token():
    s, _ = make()
    other = RevocableSerializer(
        secret_key="a-different-secret", max_age=100, max_revoked=1000, clock=Clock()
    )
    foreign = other.issue("x")
    with pytest.raises(BadSignature):
        s.revoke(foreign)


def test_is_valid_returns_plain_bool():
    s, _ = make()
    token = s.issue("x")
    assert s.is_valid(token) is True
    assert s.is_valid("not.a.real.token") is False


def test_denylist_memory_stays_bounded_as_tokens_expire():
    # Revocations are spread out over time so that earlier ones expire before
    # later ones are added. A limiter that reclaims expired entries keeps the
    # denylist small even though many tokens are revoked over the run.
    s, clock = make(max_age=100, max_revoked=10)
    for i in range(200):
        clock.set(1_000_000 + i * 50)  # 50s apart; window is 100s
        token = s.issue(f"tok-{i}")
        s.revoke(token)
    # At any instant only a couple of revocations are still within their window.
    assert len(s._revoked) <= 10


def test_reissue_after_expiry_is_independent():
    # A brand-new token issued after an old one expired is unrelated to it and
    # is valid on its own even if the old one had been revoked.
    s, clock = make(max_age=100)
    old = s.issue("session")
    s.revoke(old)
    clock.set(clock() + 200)  # old token now expired
    new = s.issue("session")
    assert s.is_valid(new) is True
