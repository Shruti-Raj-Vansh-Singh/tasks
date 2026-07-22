"""U5: a body whose decoded size is exactly ``max_size`` is accepted (the bound
is inclusive), returning the full content.

Utility requirement -- pins the off-by-one boundary so a correct bounded decoder
does not reject a body that is exactly at the limit.
"""
from kombu import compression
from kombu.safe_compression import decompress_bounded


def test_body_exactly_at_limit_accepted():
    size = 64 * 1024
    data = b"\xa5" * size
    blob, _ = compression.compress(data, "zlib")
    out = decompress_bounded(blob, "zlib", size)
    assert out == data
    assert len(out) == size
