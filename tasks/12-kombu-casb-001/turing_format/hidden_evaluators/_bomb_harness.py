"""Shared helpers for the kombu-casb-001 oracles.

Builds compressed payloads (ordinary ones and a highly-compressible
"decompression bomb") and measures the peak memory a decode holds, using the
standard-library ``tracemalloc``. Nothing here monkeypatches the module under
test; the oracles import the real ``kombu.safe_compression`` from the repo under
test and grade only observable behavior (returned bytes, raised exceptions, and
peak memory produced while decoding).
"""

from __future__ import annotations

import bz2
import tracemalloc
import zlib

# Sizes are chosen to be grader-safe: the bomb decompresses to tens of MB, big
# enough that a decode which fully materializes it is clearly distinguishable
# from a bounded one, small enough that it will not OOM a normal CI box.
CAP = 1 * 1024 * 1024                 # 1 MB documented ceiling used in grading
BOMB_PLAIN = 64 * 1024 * 1024         # 64 MB decompressed
# A safe (bounded) decode holds ~CAP bytes; a naive one holds ~BOMB_PLAIN bytes.
# The pass threshold sits well between the two.
PEAK_THRESHOLD = 16 * 1024 * 1024     # 16 MB


def zlib_bomb(plain_size=BOMB_PLAIN):
    """A small zlib blob that decompresses to ``plain_size`` bytes of zeros."""
    return zlib.compress(b"\0" * plain_size, 9)


def bz2_bomb(plain_size=BOMB_PLAIN):
    return bz2.compress(b"\0" * plain_size, 9)


def zlib_payload(data):
    return zlib.compress(data, 9)


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
