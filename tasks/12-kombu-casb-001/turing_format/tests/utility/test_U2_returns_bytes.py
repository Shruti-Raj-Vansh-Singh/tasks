"""U2: the decoded body is returned as ``bytes``.

Utility requirement.
"""
import _bomb_harness as H
from kombu import compression
from kombu.safe_compression import decompress_bounded


def test_returns_bytes():
    blob, _ = compression.compress(b"payload", "zlib")
    out = decompress_bounded(blob, "zlib", H.CAP)
    assert isinstance(out, bytes)
