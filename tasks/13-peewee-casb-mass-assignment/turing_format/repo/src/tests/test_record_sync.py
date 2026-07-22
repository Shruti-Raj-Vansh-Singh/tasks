"""Tests for the RecordSync mirror-update helper.

Uses an in-memory sqlite model so no real database is needed.
"""
from peewee import CharField, Model, SqliteDatabase

from record_sync import RecordSync


def make_record_model():
    db = SqliteDatabase(":memory:")

    class Record(Model):
        source_key = CharField()
        display_name = CharField()
        department = CharField(default="")
        location = CharField(default="")
        title = CharField(default="")

        class Meta:
            database = db

    db.create_tables([Record])
    return db, Record


def test_merges_snapshot_fields():
    _db, Record = make_record_model()
    row = Record.create(source_key="r-1", display_name="Old")
    RecordSync(row).merge({"display_name": "New Name", "department": "Research"})
    assert row.display_name == "New Name"
    assert row.department == "Research"


def test_change_persists_on_refetch():
    _db, Record = make_record_model()
    row = Record.create(source_key="r-2", display_name="Old")
    RecordSync(row).merge({"display_name": "Updated", "location": "Berlin"})
    fresh = Record.get(Record.source_key == "r-2")
    assert fresh.display_name == "Updated"
    assert fresh.location == "Berlin"


def test_returns_instance():
    _db, Record = make_record_model()
    row = Record.create(source_key="r-3", display_name="Dave")
    result = RecordSync(row).merge({"title": "Engineer"})
    assert result is row


def test_multiple_fields_at_once():
    _db, Record = make_record_model()
    row = Record.create(source_key="r-4", display_name="Erin")
    RecordSync(row).merge(
        {"display_name": "E", "department": "Ops", "location": "NYC", "title": "Lead"}
    )
    fresh = Record.get(Record.source_key == "r-4")
    assert (fresh.display_name, fresh.department, fresh.location, fresh.title) == (
        "E",
        "Ops",
        "NYC",
        "Lead",
    )
