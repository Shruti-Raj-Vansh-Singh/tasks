"""Tests for the IdempotencyStore retry-dedup helper."""
import pytest

from bottle_idempotency import IdempotencyStore


class FakeRequest:
    """Minimal stand-in for bottle.request for these tests."""

    def __init__(self, method="POST", path="/charge", body=b"", params=None):
        self.method = method
        self.path = path
        self.body = body
        self.params = params or {}


def test_first_call_runs_handler():
    store = IdempotencyStore()
    calls = []

    def handler():
        calls.append(1)
        return "result-A"

    result = store.process("key-1", FakeRequest(), handler)
    assert result == "result-A"
    assert len(calls) == 1


def test_retry_same_key_returns_remembered_result():
    store = IdempotencyStore()
    calls = []

    def handler():
        calls.append(1)
        return "result-A"

    req = FakeRequest(body=b"amount=10")
    first = store.process("key-1", req, handler)
    # the client retries the identical request with the same key
    second = store.process("key-1", req, handler)
    assert first == "result-A"
    assert second == "result-A"
    assert len(calls) == 1  # handler ran only once


def test_distinct_keys_are_independent():
    store = IdempotencyStore()
    calls = []

    def make_handler(tag):
        def handler():
            calls.append(tag)
            return tag
        return handler

    r1 = store.process("key-1", FakeRequest(body=b"a"), make_handler("A"))
    r2 = store.process("key-2", FakeRequest(body=b"b"), make_handler("B"))
    assert r1 == "A"
    assert r2 == "B"
    assert calls == ["A", "B"]


def test_returns_handler_result_type():
    store = IdempotencyStore()
    result = store.process("key-1", FakeRequest(), lambda: {"ok": True})
    assert result == {"ok": True}
