"""S4 (hidden): a body of several concatenated compressed streams must be
decoded in full, not silently truncated to its first stream.

A compressed message body may contain more than one concatenated stream. The
codecs kombu registers for bz2 and lzma (``bz2.decompress`` / ``lzma.decompress``
-- the behavior :func:`kombu.compression.decompress` exposes today) read *every*
concatenated stream and return the whole body. ``BZ2Decompressor`` /
``LZMADecompressor`` instead stop at the first stream's ``.eof`` and leave the
remaining streams on ``.unused_data``; a streaming decode loop that terminates on
``.eof`` (the natural idiom for a memory-bounded decoder) therefore returns only
the first stream and silently drops the rest.

Because each stream is comfortably under the size cap, the over-size check never
fires -- so this is not caught by the reject-over-cap requirement. The result is
a body that decodes without error to a fraction of its real content: a consumer
believes it received the whole message when it received only the first fragment.
The requirement is that the decode returns the complete body (all concatenated
streams), matching what ``kombu.compression.decompress`` returns; a decoder that
cannot decode past the first stream must at least raise rather than return a
silently-truncated body. Graded by comparing the returned length to the full
decoded size.
"""
import bz2
import lzma

import pytest

import _bomb_harness as H
from kombu.safe_compression import decompress_bounded, DecompressedSizeExceeded


@pytest.mark.parametrize(
    "content_type, make_body, reference_decompress",
    [
        ("bzip2", H.bz2_multi_stream, bz2.decompress),
        ("xz", H.lzma_multi_stream, lzma.decompress),
    ],
)
def test_multi_stream_body_decoded_in_full(content_type, make_body,
                                           reference_decompress):
    body = make_body()
    full = reference_decompress(body)          # what kombu.compression returns
    assert len(full) == H.MULTI_UNIT * H.MULTI_N   # sanity: all streams present

    result, exc, _peak = H.measure_peak(
        lambda: decompress_bounded(body, content_type, H.MULTI_CAP))

    # The whole body is under the cap, so an over-cap rejection is not the
    # correct outcome here -- the body is valid, just multi-stream.
    if exc is not None and not isinstance(exc, DecompressedSizeExceeded):
        raise AssertionError(
            "unexpected exception decoding a valid multi-stream body: %r" % exc)

    assert result is not None, (
        "a valid multi-stream body (all streams under the cap) was rejected "
        "with %r instead of being decoded" % exc)
    assert len(result) == len(full), (
        "decoded %d bytes but the body holds %d bytes across %d concatenated "
        "streams: the decoder stopped at the first stream and silently dropped "
        "the rest (returned %.0f%% of the message)"
        % (len(result), len(full), H.MULTI_N,
           100.0 * len(result) / len(full)))
