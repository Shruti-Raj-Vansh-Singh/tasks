"""U4: content_type accepts the same aliases ``kombu.compression.decompress``
does (mime type and short names), producing identical content.

Utility requirement.
"""
import pytest

import _bomb_harness as H
from kombu import compression
from kombu.safe_compression import decompress_bounded


@pytest.mark.parametrize(
    "compress_as, decode_as",
    [
        ("gzip", "application/x-gzip"),
        ("zlib", "gzip"),
        ("bzip2", "application/x-bz2"),
        ("bzip2", "bzip"),
    ],
)
def test_accepts_alias(compress_as, decode_as):
    data = b"alias check " * 200
    blob, _ = compression.compress(data, compress_as)
    out = decompress_bounded(blob, decode_as, H.CAP)
    assert out == data
