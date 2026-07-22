"""U2: merged fields are persisted to the database and a partial snapshot leaves
untouched descriptive fields intact."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_change_persists_on_refetch():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u2", display_name="Old")
    RecordSync(row).merge({"display_name": "Persisted", "location": "Rome"})
    fresh = Record.get(Record.source_key == "u2")
    assert fresh.display_name == "Persisted"
    assert fresh.location == "Rome"


def test_partial_snapshot_leaves_other_fields():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u2b", display_name="Keep", department="R&D")
    RecordSync(row).merge({"location": "Oslo"})
    fresh = Record.get(Record.source_key == "u2b")
    assert fresh.location == "Oslo"
    assert fresh.display_name == "Keep"
    assert fresh.department == "R&D"
