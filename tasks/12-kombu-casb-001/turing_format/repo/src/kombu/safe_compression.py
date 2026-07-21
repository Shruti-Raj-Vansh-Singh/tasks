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


class DecompressedSizeExceeded(ValueError):
    """Raised when a body would decompress to more than ``max_size`` bytes."""


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
    raise NotImplementedError('decompress_bounded is not implemented yet')
