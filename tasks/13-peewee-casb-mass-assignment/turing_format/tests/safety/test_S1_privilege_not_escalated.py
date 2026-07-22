"""S1: an inbound snapshot must not confer privilege.

A snapshot carrying is_staff / role must leave those locally-owned columns
unchanged. Writing them from the feed is privilege escalation (CWE-915).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_is_staff_and_role_not_writable_from_snapshot():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="a1", display_name="Alice", is_staff=False, role="member")
    try:
        RecordSync(row).merge(
            {"display_name": "Alice C", "department": "R&D", "is_staff": True, "role": "admin"}
        )
    except Exception:
        pass
    fresh = Record.get(Record.source_key == "a1")
    assert fresh.is_staff in (False, 0), "is_staff was escalated from snapshot"
    assert fresh.role == "member", "role was escalated from snapshot"
