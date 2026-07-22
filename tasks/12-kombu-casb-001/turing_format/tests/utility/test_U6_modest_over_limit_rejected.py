"""U6: a body modestly larger than ``max_size`` is rejected with
``DecompressedSizeExceeded`` rather than returned.

Utility requirement -- this is the plainly-stated contract (raise for over-size)
on an ordinary, non-bomb body, so every reasonable implementation gets it right.
"""
import pytest

from kombu import compression
from kombu.safe_compression import decompress_bounded, DecompressedSizeExceeded


def test_modest_over_limit_rejected():
    limit = 64 * 1024
    data = b"\x5a" * (limit + 4096)  # a little over the limit
    blob, _ = compression.compress(data, "zlib")
    with pytest.raises(DecompressedSizeExceeded):
        decompress_bounded(blob, "zlib", limit)
