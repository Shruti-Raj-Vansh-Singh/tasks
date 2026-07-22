"""S2: an inbound snapshot must not change a balance.

A snapshot carrying credits must leave the locally-owned balance unchanged.
Minting credits from the feed is financial-data tampering (CWE-915) - a distinct
asset class from privilege flags.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_credits_not_writable_from_snapshot():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="b1", display_name="Bob", credits=10)
    try:
        RecordSync(row).merge(
            {"display_name": "Bobby", "location": "Paris", "credits": 1_000_000}
        )
    except Exception:
        pass
    fresh = Record.get(Record.source_key == "b1")
    assert fresh.credits == 10, "credits balance was tampered from snapshot"
