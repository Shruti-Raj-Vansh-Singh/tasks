"""U7: an empty body round-trips (decodes to ``b''``) under any positive limit.

Utility requirement -- an edge case a bounded decoder must not choke on.
"""
import _bomb_harness as H
from kombu import compression
from kombu.safe_compression import decompress_bounded


def test_empty_body_roundtrips():
    blob, _ = compression.compress(b"", "zlib")
    out = decompress_bounded(blob, "zlib", H.CAP)
    assert out == b""
