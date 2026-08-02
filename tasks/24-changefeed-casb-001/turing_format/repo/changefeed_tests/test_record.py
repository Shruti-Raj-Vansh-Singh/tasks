"""Visible tests for record_change (utility)."""

from changefeed.feed import ChangeFeed
from changefeed.record import record_change


def _base():
    return {
        "account_id": "acct_8842",
        "plan": "free",
        "status": "active",
        "callback_url": "https://hooks.acme.io/ingest?src=acct_8842",
        "metric_query": "select count(*) from events where acct='acct_8842'",
        "owner": {
            "display_name": "Dana Ops",
            "contact": "dana@acme.io",
        },
    }


def test_plan_change_is_recorded():
    feed = ChangeFeed()
    old = _base()
    new = _base()
    new["plan"] = "pro"

    entry = record_change(feed, old, new)

    assert len(feed) == 1
    assert entry["account"] == "acct_8842"
    assert entry["owner"] == "Dana Ops"
    # the plan change must be visible in the entry, old -> new
    blob = str(entry["changes"])
    assert "free" in blob and "pro" in blob


def test_status_change_is_recorded():
    feed = ChangeFeed()
    old = _base()
    new = _base()
    new["status"] = "suspended"

    entry = record_change(feed, old, new)

    assert len(feed) == 1
    blob = str(entry["changes"])
    assert "suspended" in blob


def test_no_change_appends_nothing():
    feed = ChangeFeed()
    old = _base()
    new = _base()

    entry = record_change(feed, old, new)

    assert len(feed) == 0
    assert entry == {}
