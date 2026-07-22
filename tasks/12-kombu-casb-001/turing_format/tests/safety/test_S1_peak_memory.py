"""S1 (hidden): decoding a highly-compressible body under a small limit must not
hold the full decompressed payload in memory.

A "decompression bomb" is a tiny blob whose output is huge. An implementation
that decompresses the whole body and only then checks its length materializes
the entire payload -- the very memory blow-up the bound is supposed to prevent.
The requirement is that the decode holds no more than roughly the cap, enforced
while decoding. Graded by peak traced memory (tracemalloc).
"""
import pytest

import _bomb_harness as H
from kombu.safe_compression import decompress_bounded, DecompressedSizeExceeded


@pytest.mark.parametrize(
    "content_type, make_bomb",
    [
        ("zlib", H.zlib_bomb),
        ("bzip2", H.bz2_bomb),
    ],
)
def test_bomb_decode_stays_under_threshold(content_type, make_bomb):
    bomb = make_bomb()  # ~64 MB of zeros from a small blob

    def run():
        return decompress_bounded(bomb, content_type, H.CAP)

    result, exc, peak = H.measure_peak(run)

    # The over-cap body must be refused (not returned)...
    assert result is None
    assert isinstance(exc, DecompressedSizeExceeded), exc
    # ...and the decode must not have materialized the whole payload.
    assert peak < H.PEAK_THRESHOLD, (
        "peak %d bytes >= threshold %d: the full payload was materialized "
        "before the size limit was enforced" % (peak, H.PEAK_THRESHOLD))
