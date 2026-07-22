from __future__ import annotations

import pytest

from kombu import compression
from kombu.safe_compression import (
    DecompressedSizeExceeded,
    decompress_bounded,
)


class test_safe_compression:

    def test_roundtrip_within_limit_zlib(self):
        text = b'The Quick Brown Fox Jumps Over The Lazy Dog'
        blob, ctype = compression.compress(text, 'zlib')
        out = decompress_bounded(blob, ctype, max_size=1024)
        assert out == text

    def test_returns_bytes(self):
        blob, ctype = compression.compress(b'payload', 'zlib')
        out = decompress_bounded(blob, ctype, max_size=1024)
        assert isinstance(out, bytes)

    def test_roundtrip_bzip2(self):
        text = b'The Brown Quick Fox Over The Lazy Dog Jumps'
        blob, ctype = compression.compress(text, 'bzip2')
        out = decompress_bounded(blob, ctype, max_size=1024)
        assert out == text

    def test_accepts_by_alias_gzip(self):
        text = b'x' * 500
        blob, ctype = compression.compress(text, 'gzip')
        out = decompress_bounded(blob, 'gzip', max_size=4096)
        assert out == text

    def test_at_limit_is_accepted(self):
        # A body whose decompressed size is exactly max_size must be returned.
        text = b'a' * 1000
        blob, _ = compression.compress(text, 'zlib')
        out = decompress_bounded(blob, 'zlib', max_size=1000)
        assert out == text

    def test_over_limit_raises(self):
        # A modest, ordinary payload that is a little over the limit must be
        # rejected with DecompressedSizeExceeded.
        text = b'b' * 5000
        blob, _ = compression.compress(text, 'zlib')
        with pytest.raises(DecompressedSizeExceeded):
            decompress_bounded(blob, 'zlib', max_size=1000)

    def test_exceeded_is_value_error(self):
        assert issubclass(DecompressedSizeExceeded, ValueError)

    def test_empty_body_within_limit(self):
        blob, ctype = compression.compress(b'', 'zlib')
        out = decompress_bounded(blob, ctype, max_size=64)
        assert out == b''
