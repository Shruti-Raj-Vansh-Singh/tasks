"""Size-bounded decompression for message bodies.

:func:`kombu.compression.decompress` hands a body straight to the codec for its
``content_type`` and returns whatever comes out. This module adds an opt-in
variant that also takes a ``max_size``: it returns the fully decompressed body
when it is within that size, and raises :class:`DecompressedSizeExceeded` when
the body is larger than the caller is willing to accept. It is useful for
consumers that want a firm upper bound on the size of a decompressed body.

It is not wired into the normal :class:`~kombu.Message` decode path; a consumer
that wants the bound calls :func:`decompress_bounded` itself with the body,
the content type, and the maximum size it is willing to accept.

Example::

    from kombu.safe_compression import decompress_bounded, DecompressedSizeExceeded

    try:
        body = decompress_bounded(raw, 'zlib', max_size=8 * 1024 * 1024)
    except DecompressedSizeExceeded:
        # the body would decompress to more than we are willing to accept
        reject(raw)

The function returns the decompressed body as ``bytes`` (mirroring
:func:`kombu.compression.decompress`) when it is within ``max_size``. Like
:func:`kombu.compression.decompress`, it returns the complete body the codec
would produce -- a compressed body may hold more than one concatenated stream,
and every one of them is part of the message.
"""

from __future__ import annotations

import bz2
import zlib

from kombu.compression import get_decoder

try:
    import lzma
except ImportError:  # pragma: no cover
    lzma = None

try:
    from kombu.compression import _aliases
except ImportError:  # pragma: no cover
    _aliases = {}


class DecompressedSizeExceeded(ValueError):
    """Raised when a body would decompress to more than ``max_size`` bytes."""


class UnsupportedCompression(ValueError):
    """Raised for a content type this bounded decoder will not handle."""


# The codecs this bounded decoder is willing to handle. A content type outside
# this set is refused rather than passed to an unbounded fallback -- the whole
# point of the bound is that we do not run an arbitrary codec on an untrusted
# body just because it happens to be registered.
_SUPPORTED = {'application/x-gzip', 'application/x-bz2', 'application/x-lzma'}

# A ceiling on the codec's own working memory (not just its output). The LZMA
# container can request a very large dictionary in its header; capping the
# decompressor's memory keeps a body that decodes to little output from
# allocating hundreds of MB just to hold that dictionary.
_CODEC_MEMLIMIT = 64 * 1024 * 1024

_CHUNK = 64 * 1024


def _guard(out, max_size):
    if len(out) > max_size:
        raise DecompressedSizeExceeded(
            'decompressed body exceeds max_size=%d bytes' % max_size)


def _decode_zlib(body, max_size):
    """Decode a zlib stream under ``max_size``.

    Reads incrementally with ``max_length`` so a highly-compressible body never
    materializes past the cap. Mirrors :func:`zlib.decompress` (the codec kombu
    registers for ``application/x-gzip``), which reads a single zlib stream.
    """
    out = bytearray()
    d = zlib.decompressobj()
    tail = body
    while True:
        want = (max_size - len(out)) + 1
        out += d.decompress(tail, want)
        _guard(out, max_size)
        tail = d.unconsumed_tail
        if not tail:
            out += d.flush()
            _guard(out, max_size)
            return bytes(out)


def _decode_incremental_all(make_decompressor, body, max_size):
    """Decode every concatenated bz2/lzma stream in ``body`` under ``max_size``.

    ``BZ2Decompressor`` / ``LZMADecompressor`` stop at the first stream's EOF and
    expose the remainder on ``.unused_data``; a fresh decompressor is started on
    that remainder so the full body is returned. Output is pulled with
    ``max_length`` so peak memory stays near the cap.
    """
    out = bytearray()
    data = bytes(body)
    while data:
        d = make_decompressor()
        pos = 0
        while not d.eof:
            if d.needs_input:
                if pos >= len(data):
                    break
                feed = data[pos:pos + _CHUNK]
                pos += len(feed)
            else:
                feed = b''
            want = (max_size - len(out)) + 1
            out += d.decompress(feed, want)
            _guard(out, max_size)
        data = d.unused_data if d.eof else b''
    return bytes(out)


def _make_lzma():
    # memlimit bounds the codec's working memory: an xz stream whose header
    # declares a huge dictionary raises LZMAError here instead of allocating it.
    return lzma.LZMADecompressor(memlimit=_CODEC_MEMLIMIT)


def decompress_bounded(body, content_type, max_size):
    """Decompress ``body`` for ``content_type`` under a ``max_size`` ceiling.

    Arguments:
    ---------
        body (bytes): the compressed message body.
        content_type (str): mime-type / alias of the compression method used,
            the same values :func:`kombu.compression.decompress` accepts
            (for example ``'zlib'``, ``'gzip'``, ``'bzip2'``).
        max_size (int): the maximum number of bytes the decompressed body is
            allowed to occupy.

    Returns:
    -------
        bytes: the complete decompressed body, when it is at most ``max_size``
            bytes.

    Raises:
    ------
        DecompressedSizeExceeded: if the body would decompress to more than
            ``max_size`` bytes, or would require more codec working memory than
            allowed.
    """
    resolved = _aliases.get(content_type, content_type)
    if resolved == 'application/x-gzip':
        return _decode_zlib(body, max_size)
    if resolved == 'application/x-bz2':
        return _decode_incremental_all(bz2.BZ2Decompressor, body, max_size)
    if resolved == 'application/x-lzma' and lzma is not None:
        try:
            return _decode_incremental_all(_make_lzma, body, max_size)
        except lzma.LZMAError as exc:
            raise DecompressedSizeExceeded(
                'decompression exceeded the codec memory limit') from exc

    raise UnsupportedCompression(
        'unsupported content_type for bounded decompression: %r' % (content_type,))
