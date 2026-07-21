"""Size-bounded decompression for message bodies.

:func:`kombu.compression.decompress` hands a body straight to the codec for its
``content_type`` and returns whatever comes out. This module adds an opt-in
variant that also takes a ``max_size``: it returns the decompressed body when it
is within that size, and raises :class:`DecompressedSizeExceeded` when the body
is larger than the caller is willing to accept. It is useful for consumers that
want a firm upper bound on the size of a decompressed body.

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
:func:`kombu.compression.decompress`) when it is within ``max_size``.
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


def _read_bounded(feed, body, max_size):
    """Drive an incremental decompressor, holding at most ``max_size`` + 1 bytes.

    ``feed(chunk, limit)`` is a callable that returns up to ``limit`` freshly
    decompressed bytes and stores any not-yet-consumed input internally,
    exposed via the closure's own bookkeeping. It returns ``(output, more)``
    where ``more`` is truthy while decoding can continue.
    """
    out = bytearray()
    chunk, more = feed(body, max_size + 1)
    out += chunk
    while more and len(out) <= max_size:
        chunk, more = feed(b'', max_size + 1 - len(out))
        out += chunk
    if len(out) > max_size:
        raise DecompressedSizeExceeded(
            'decompressed body exceeds max_size=%d bytes' % max_size)
    return bytes(out)


def _zlib_reader():
    d = zlib.decompressobj()
    pending = {'tail': b''}

    def feed(data, limit):
        source = data if data else pending['tail']
        chunk = d.decompress(source, limit)
        pending['tail'] = d.unconsumed_tail
        more = bool(d.unconsumed_tail)
        return chunk, more
    return feed


def _bz2_reader():
    d = bz2.BZ2Decompressor()

    def feed(data, limit):
        chunk = d.decompress(data, limit)
        more = not d.eof and d.needs_input is False
        return chunk, more
    return feed


def _lzma_reader():
    d = lzma.LZMADecompressor()

    def feed(data, limit):
        chunk = d.decompress(data, limit)
        more = not d.eof
        return chunk, more
    return feed


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
        bytes: the decompressed body, when it is at most ``max_size`` bytes.

    Raises:
    ------
        DecompressedSizeExceeded: if the body would decompress to more than
            ``max_size`` bytes.
    """
    resolved = _aliases.get(content_type, content_type)
    if resolved == 'application/x-gzip':
        return _read_bounded(_zlib_reader(), body, max_size)
    if resolved == 'application/x-bz2':
        return _read_bounded(_bz2_reader(), body, max_size)
    if resolved == 'application/x-lzma' and lzma is not None:
        return _read_bounded(_lzma_reader(), body, max_size)

    # Any other registered codec: fall back to the module decoder. This branch
    # does not bound memory and is only reached for codecs without an
    # incremental reader here; the documented, supported codecs above are the
    # bounded ones.
    out = get_decoder(content_type)(body)
    if len(out) > max_size:
        raise DecompressedSizeExceeded(
            'decompressed body exceeds max_size=%d bytes' % max_size)
    return out
