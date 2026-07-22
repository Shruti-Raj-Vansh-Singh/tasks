"""U1: descriptive fields present in the snapshot are written onto the row and
merge returns the updated instance. Uses only feed-owned fields."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model, merge_not_implemented  # noqa: E402


def test_single_field_merged():
    assert not merge_not_implemented(), "RecordSync.merge is unimplemented"
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u1", display_name="Old")
    RecordSync(row).merge({"display_name": "New"})
    assert row.display_name == "New"


def test_multiple_fields_merged():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u1b", display_name="Old")
    RecordSync(row).merge(
        {"display_name": "X", "department": "Ops", "location": "NYC", "title": "Lead"}
    )
    assert (row.display_name, row.department, row.location, row.title) == (
        "X",
        "Ops",
        "NYC",
        "Lead",
    )


def test_merge_returns_instance():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u1c", display_name="Old")
    assert RecordSync(row).merge({"title": "Eng"}) is row
