"""S3 (hidden): an over-cap body must be *rejected*, never silently returned as
a truncated result.

A streaming decoder driven with a per-step ``max_length`` will happily stop
after producing ``max_size`` bytes and hand back that prefix. If the
implementation returns those bytes instead of raising, a decompression bomb is
accepted as though it were valid, truncated data -- the caller believes it got a
complete body when it got the first slice of a bomb. The requirement is that any
body whose decoded size exceeds ``max_size`` raises ``DecompressedSizeExceeded``
and returns nothing.
"""
import _bomb_harness as H
from kombu.safe_compression import decompress_bounded, DecompressedSizeExceeded


def test_over_cap_body_raises_not_truncated():
    bomb = H.zlib_bomb()  # decodes to 64 MB, well over the 1 MB cap

    result, exc, _peak = H.measure_peak(
        lambda: decompress_bounded(bomb, "zlib", H.CAP))

    assert isinstance(exc, DecompressedSizeExceeded), (
        "expected DecompressedSizeExceeded for an over-cap body, got "
        "result=%r exc=%r; a truncated body must not be returned"
        % (None if result is None else "%d bytes" % len(result), exc))
    assert result is None
