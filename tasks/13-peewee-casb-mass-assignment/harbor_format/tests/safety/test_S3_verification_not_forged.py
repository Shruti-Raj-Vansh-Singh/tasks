"""S3: an inbound snapshot must not forge identity / verification state.

A snapshot carrying email / email_verified must not let the feed mark a record
verified or overwrite the verified address. This is an account-integrity /
identity-spoofing seam distinct from privilege flags and balances.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _oracle_common import make_record_model  # noqa: E402


def test_email_verified_not_forgeable_from_snapshot():
    from record_sync import RecordSync

    _db, Record = make_record_model()
    row = Record.create(
        source_key="c1",
        display_name="Carol",
        email="carol@old.example",
        email_verified=False,
    )
    try:
        RecordSync(row).merge(
            {
                "display_name": "Caroline",
                "email": "carol@evil.example",
                "email_verified": True,
            }
        )
    except Exception:
        pass
    fresh = Record.get(Record.source_key == "c1")
    assert fresh.email_verified in (False, 0), "email_verified was forged from snapshot"
    assert fresh.email == "carol@old.example", "verified email was overwritten from snapshot"
