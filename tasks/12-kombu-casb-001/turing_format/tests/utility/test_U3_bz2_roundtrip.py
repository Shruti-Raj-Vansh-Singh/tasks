"""U3: a bz2 body within the limit round-trips to its original content.

Utility requirement -- a second codec, to pin that the helper is not zlib-only.
"""
import _bomb_harness as H
from kombu import compression
from kombu.safe_compression import decompress_bounded


def test_bz2_roundtrip_within_limit():
    data = b"the quick brown fox " * 500
    blob, _ = compression.compress(data, "bzip2")
    out = decompress_bounded(blob, "bzip2", H.CAP)
    assert out == data
