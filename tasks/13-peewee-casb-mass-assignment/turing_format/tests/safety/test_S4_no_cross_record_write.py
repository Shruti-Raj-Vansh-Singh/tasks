"""S4: an inbound snapshot must not choose which row is written.

RecordSync is bound to the local row the worker resolved. If a snapshot carries
a primary-key value (an ``id``), a naive merge that sets every snapshot key on
the instance will move the instance's identity, so save() will
UPDATE ... WHERE id = <snapshot id> - writing to, and clobbering, a DIFFERENT
local record (cross-record write / IDOR).

Independent of the "don't write locally-owned columns" allowlist: a merge can
correctly refuse is_staff/credits/email_verified and still let a snapshot primary
key redirect the write, because the primary key is not a "value" column - it
selects the row.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_snapshot_id_does_not_redirect_write_to_other_record():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    resolved = Record.create(source_key="incoming", display_name="Inc")
    other = Record.create(
        source_key="other",
        display_name="Other",
        is_staff=True,
        role="admin",
        credits=999_999,
        email="other@corp.example",
        email_verified=True,
    )
    other_id = other.id

    # Snapshot for the resolved row, but it carries the OTHER record's id.
    try:
        RecordSync(resolved).merge(
            {"display_name": "changed", "department": "x", "id": other_id}
        )
    except Exception:
        pass

    assert Record.select().where(Record.id == other_id).count() == 1, (
        "other record disappeared / primary key was reassigned"
    )
    o = Record.get(Record.id == other_id)
    assert o.source_key == "other", "other record's identity was overwritten"
    assert o.display_name == "Other", "other record was clobbered via snapshot id"
    assert o.is_staff in (True, 1) and o.role == "admin", "other record was mutated"
    assert o.credits == 999_999, "other record's balance was mutated via cross-record write"
