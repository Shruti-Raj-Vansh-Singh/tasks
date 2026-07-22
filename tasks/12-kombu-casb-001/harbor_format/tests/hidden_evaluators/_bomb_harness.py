"""Shared helpers for the kombu-casb-001 oracles.

Builds compressed payloads (ordinary ones and several kinds of decompression
bomb) and measures the peak memory a decode holds, using the standard-library
``tracemalloc``. Nothing here monkeypatches the module under test; the oracles
import the real ``kombu.safe_compression`` from the repo under test and grade
only observable behavior (returned bytes, raised exceptions, and peak memory
produced while decoding).

Three distinct bombs back the three safety requirements:

* :func:`zlib_bomb` / :func:`bz2_bomb` -- ordinary highly-compressible bodies
  whose *output* is large (tens of MB from a tiny blob). A decode that
  materializes the whole output before checking its size peaks at the full
  output size; a decode that reads incrementally under the cap does not. (S1)

* :func:`xz_dict_bomb` -- a tiny xz stream (under 100 bytes) whose container
  header declares a very large LZMA *dictionary*. The memory is allocated for
  the dictionary, independently of how much output is produced, so even a
  correct output-bounded streaming loop peaks at the dictionary size unless it
  also bounds the codec's working memory (``LZMADecompressor(memlimit=...)``)
  or refuses the codec outright. (S2)

* :func:`zlib_bomb` under a small cap also drives S3: a decode that streams and
  simply stops at ``max_size`` returns a truncated body with no error, silently
  accepting a bomb as if it were valid data. The requirement is that an
  over-cap body is rejected, not truncated. (S3)
"""

from __future__ import annotations

import bz2
import lzma
import tracemalloc
import zlib

# Sizes are chosen to be grader-safe: the output bombs decompress to tens of MB
# and the xz dictionary bomb allocates a few hundred MB, both big enough that a
# decode which fully materializes them is clearly distinguishable from a bounded
# one, and small enough not to OOM a normal CI box (container budget is several
# GB; the largest peak here is ~270 MB).
CAP = 1 * 1024 * 1024                 # 1 MB documented ceiling used in grading
BOMB_PLAIN = 64 * 1024 * 1024         # 64 MB decompressed output
PEAK_THRESHOLD = 16 * 1024 * 1024     # 16 MB -- a bounded decode stays well under

# The dictionary the xz bomb declares in its stream header. Independent of the
# ~4 KB of output it actually produces; a decode that does not cap codec working
# memory allocates this much.
XZ_DICT_SIZE = 256 * 1024 * 1024      # 256 MB


def zlib_bomb(plain_size=BOMB_PLAIN):
    """A small zlib blob that decompresses to ``plain_size`` bytes of zeros."""
    return zlib.compress(b"\0" * plain_size, 9)


def bz2_bomb(plain_size=BOMB_PLAIN):
    return bz2.compress(b"\0" * plain_size, 9)


def xz_dict_bomb(dict_size=XZ_DICT_SIZE):
    """A tiny xz stream whose header declares a ``dict_size``-byte dictionary.

    Decompresses to only ~4 KB of output, but a decoder that does not bound its
    working memory allocates ``dict_size`` bytes to hold the dictionary. Used to
    show that bounding *output* size is not enough to bound *memory*.
    """
    return lzma.compress(
        b"\0" * 4096,
        format=lzma.FORMAT_XZ,
        filters=[{"id": lzma.FILTER_LZMA2, "preset": 9, "dict_size": dict_size}],
    )


def zlib_payload(data):
    return zlib.compress(data, 9)


def bz2_payload(data):
    return bz2.compress(data, 9)


def lzma_payload(data):
    return lzma.compress(data)


# A single message body may hold more than one concatenated compressed stream:
# ``bz2.decompress`` / ``lzma.decompress`` (the codecs kombu registers) read
# *every* concatenated stream and return the whole thing. These builders make a
# body of ``n`` concatenated streams whose total decoded size is well under a
# grading cap, so an over-cap size check never fires -- the only way the full
# body comes back is a decoder that continues past the first stream's EOF.
MULTI_UNIT = 200 * 1024   # 200 KB per stream
MULTI_N = 5               # 5 streams -> ~1 MB total (under the 2 MB cap below)
MULTI_CAP = 2 * 1024 * 1024


def bz2_multi_stream(unit=MULTI_UNIT, n=MULTI_N):
    """``n`` concatenated bz2 streams, ``unit`` bytes each. ``bz2.decompress``
    returns all ``unit * n`` bytes; a first-stream-only decoder returns ``unit``.
    """
    return bz2.compress(b"A" * unit, 9) * n


def lzma_multi_stream(unit=MULTI_UNIT, n=MULTI_N):
    """``n`` concatenated xz streams, ``unit`` bytes each. ``lzma.decompress``
    returns all ``unit * n`` bytes; a first-stream-only decoder returns ``unit``.
    """
    return lzma.compress(b"A" * unit) * n


def measure_peak(fn):
    """Run ``fn`` and return (result, exception, peak_bytes).

    ``result`` is the return value (or None on exception); ``exception`` is the
    raised exception instance (or None); ``peak_bytes`` is the peak traced
    memory during the call.
    """
    tracemalloc.start()
    result = None
    exc = None
    try:
        result = fn()
    except BaseException as e:  # noqa: BLE001 - we report whatever happens
        exc = e
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, exc, peak
