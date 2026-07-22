"""U3: ordinary snapshot shapes merge without error - an empty snapshot is a
clean no-op and repeated merges accumulate feed edits."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_empty_snapshot_is_noop():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u3", display_name="Keep", department="D")
    RecordSync(row).merge({})
    fresh = Record.get(Record.source_key == "u3")
    assert fresh.display_name == "Keep"
    assert fresh.department == "D"


def test_repeated_merge_accumulates():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(source_key="u3b", display_name="A")
    RecordSync(row).merge({"display_name": "B"})
    RecordSync(row).merge({"department": "Ops"})
    fresh = Record.get(Record.source_key == "u3b")
    assert fresh.display_name == "B"
    assert fresh.department == "Ops"
