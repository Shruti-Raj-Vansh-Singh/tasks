"""Tests for the ProfileUpdater profile-edit helper.

Uses an in-memory sqlite model so no real database is needed.
"""
from peewee import CharField, Model, SqliteDatabase

from profile_service import ProfileUpdater


def make_account_model():
    db = SqliteDatabase(":memory:")

    class Account(Model):
        username = CharField()
        display_name = CharField()
        bio = CharField(default="")
        location = CharField(default="")
        website = CharField(default="")

        class Meta:
            database = db

    db.create_tables([Account])
    return db, Account


def test_applies_submitted_fields():
    _db, Account = make_account_model()
    acct = Account.create(username="bob", display_name="Bob")
    ProfileUpdater(acct).apply({"display_name": "Bobby", "bio": "hello there"})
    assert acct.display_name == "Bobby"
    assert acct.bio == "hello there"


def test_change_persists_on_refetch():
    _db, Account = make_account_model()
    acct = Account.create(username="carol", display_name="Carol")
    ProfileUpdater(acct).apply({"display_name": "Caroline", "location": "Berlin"})
    fresh = Account.get(Account.username == "carol")
    assert fresh.display_name == "Caroline"
    assert fresh.location == "Berlin"


def test_returns_instance():
    _db, Account = make_account_model()
    acct = Account.create(username="dave", display_name="Dave")
    result = ProfileUpdater(acct).apply({"bio": "hi"})
    assert result is acct


def test_multiple_editable_fields_at_once():
    _db, Account = make_account_model()
    acct = Account.create(username="erin", display_name="Erin")
    ProfileUpdater(acct).apply(
        {"display_name": "E", "bio": "b", "location": "NYC", "website": "e.example"}
    )
    fresh = Account.get(Account.username == "erin")
    assert (fresh.display_name, fresh.bio, fresh.location, fresh.website) == (
        "E",
        "b",
        "NYC",
        "e.example",
    )
