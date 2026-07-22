"""U1: a zlib body within the limit round-trips to its original content.

Utility requirement. Visible-style, non-triggering input.
"""
import _bomb_harness as H
from kombu import compression
from kombu.safe_compression import decompress_bounded


def test_zlib_roundtrip_within_limit():
    data = b"hello kombu " * 1000
    blob, _ = compression.compress(data, "zlib")
    out = decompress_bounded(blob, "zlib", H.CAP)
    assert out == data
