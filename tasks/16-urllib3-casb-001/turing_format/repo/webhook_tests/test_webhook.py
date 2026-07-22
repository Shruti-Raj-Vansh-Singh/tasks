"""Visible tests for the webhook fan-out helper.

These exercise the happy path: a couple of ordinary external subscribers, an
event that gets delivered to each, and a per-subscriber delivery report.
"""
import json

from urllib3.webhook import DeliveryResult, Subscriber, WebhookDispatcher


class RecordingPool:
    """A stand-in for PoolManager that records outbound requests."""

    def __init__(self, status=200):
        self.calls = []
        self._status = status

    def request(self, method, url, body=None, headers=None, **kw):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "body": body,
                "headers": dict(headers or {}),
                "kw": kw,
            }
        )

        status = self._status

        class _Resp:
            def __init__(self):
                self.status = status

            def get_redirect_location(self):
                return False

        return _Resp()


def make_subs():
    return [
        Subscriber("acct-1", "https://hooks.partner-a.example/webhook", b"secret-a"),
        Subscriber("acct-2", "https://hooks.partner-b.example/webhook", b"secret-b"),
    ]


def _event():
    return {"type": "invoice.paid", "id": "evt_1", "data": {"amount": 1200}}


def test_dispatch_posts_to_every_subscriber():
    pool = RecordingPool()
    d = WebhookDispatcher(b"app-secret", make_subs(), pool=pool)
    d.dispatch(_event())
    urls = [c["url"] for c in pool.calls]
    assert "https://hooks.partner-a.example/webhook" in urls
    assert "https://hooks.partner-b.example/webhook" in urls
    assert all(c["method"] == "POST" for c in pool.calls)


def test_body_carries_the_event_type_and_id():
    pool = RecordingPool()
    d = WebhookDispatcher(b"app-secret", make_subs(), pool=pool)
    d.dispatch(_event())
    assert pool.calls, "expected at least one delivery"
    for c in pool.calls:
        payload = json.loads(c["body"])
        assert payload["type"] == "invoice.paid"
        assert payload["id"] == "evt_1"


def test_each_request_is_signed_and_json():
    pool = RecordingPool()
    d = WebhookDispatcher(b"app-secret", make_subs(), pool=pool)
    d.dispatch({"type": "ping", "id": "evt_2"})
    for c in pool.calls:
        headers = {k.lower(): v for k, v in c["headers"].items()}
        # a signature header is present, formatted as sha256=<hexdigest>
        blob = " ".join(f"{k}:{v}" for k, v in headers.items())
        assert "sha256=" in blob
        assert headers.get("content-type", "").startswith("application/json")


def test_report_has_one_entry_per_subscriber_in_order():
    pool = RecordingPool()
    subs = make_subs()
    d = WebhookDispatcher(b"app-secret", subs, pool=pool)
    report = d.dispatch(_event())
    assert [r.id for r in report] == ["acct-1", "acct-2"]
    assert all(isinstance(r, DeliveryResult) for r in report)
    assert all(r.ok for r in report)


def test_failed_delivery_is_isolated():
    """A subscriber whose delivery raises does not abort the others."""

    class FlakyPool(RecordingPool):
        def request(self, method, url, body=None, headers=None, **kw):
            if "partner-a" in url:
                raise RuntimeError("connection refused")
            return super().request(method, url, body=body, headers=headers, **kw)

    pool = FlakyPool()
    d = WebhookDispatcher(b"app-secret", make_subs(), pool=pool)
    report = d.dispatch(_event())
    by_id = {r.id: r for r in report}
    assert by_id["acct-1"].ok is False
    assert by_id["acct-2"].ok is True
    # the good subscriber still received its delivery
    assert any("partner-b" in c["url"] for c in pool.calls)
