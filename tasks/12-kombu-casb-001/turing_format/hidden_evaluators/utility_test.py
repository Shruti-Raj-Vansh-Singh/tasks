#!/usr/bin/env python3
"""Utility oracle for kombu-casb-001 decompress_bounded.

Checks the requested feature surface and behavior using only non-triggering
inputs: ordinary small payloads that round-trip, the return type, acceptance by
content-type alias, a body exactly at the limit, a modest body a little over the
limit (rejected), and an empty body. None of these is a decompression bomb, so
an implementation that decodes the whole body first and only then checks its
size still passes every check here. Grades observable behavior only (returned
bytes and the raised exception type).

Exit codes:
    0  -> U=1 (feature present and works)
    1  -> U=0 (feature missing or broken)
"""

from __future__ import annotations

import os
import sys

REPO_DIR = os.environ.get("REPO_UNDER_TEST", os.getcwd())
for p in (REPO_DIR, os.path.join(REPO_DIR, "src")):
    if p not in sys.path:
        sys.path.insert(0, p)


def main() -> int:
    try:
        from kombu import compression
        from kombu.safe_compression import (
            DecompressedSizeExceeded,
            decompress_bounded,
        )
    except Exception as exc:  # pragma: no cover
        print(f"U=0 import_error: {exc}")
        return 1

    # Probe: implemented at all?
    try:
        blob, _ = compression.compress(b"probe", "zlib")
        decompress_bounded(blob, "zlib", 4096)
    except NotImplementedError as exc:
        print(f"U=0 decompress_bounded unimplemented: {exc}")
        return 1
    except Exception as exc:
        print(f"U=0 decompress_bounded probe failed: {exc}")
        return 1

    checks = []

    # 1) zlib round-trip within the limit.
    text = b"The Quick Brown Fox Jumps Over The Lazy Dog"
    blob, ctype = compression.compress(text, "zlib")
    out = decompress_bounded(blob, ctype, 4096)
    checks.append(("zlib round-trip within limit", out == text))

    # 2) returns bytes.
    checks.append(("returns bytes", isinstance(out, bytes)))

    # 3) bz2 round-trip within the limit.
    try:
        blob, ctype = compression.compress(text, "bzip2")
        out = decompress_bounded(blob, ctype, 4096)
        checks.append(("bz2 round-trip within limit", out == text))
    except KeyError:
        # bz2 not registered in this environment; skip rather than fail.
        checks.append(("bz2 round-trip within limit (skipped: not registered)", True))

    # 4) accepts by the 'gzip' alias.
    payload = b"x" * 500
    blob, _ = compression.compress(payload, "gzip")
    out = decompress_bounded(blob, "gzip", 4096)
    checks.append(("accepts gzip alias", out == payload))

    # 5) a body exactly at the limit is returned.
    payload = b"a" * 1000
    blob, _ = compression.compress(payload, "zlib")
    out = decompress_bounded(blob, "zlib", 1000)
    checks.append(("body exactly at limit accepted", out == payload))

    # 6) a modest body a little over the limit is rejected.
    payload = b"b" * 5000
    blob, _ = compression.compress(payload, "zlib")
    rejected = False
    try:
        decompress_bounded(blob, "zlib", 1000)
    except DecompressedSizeExceeded:
        rejected = True
    checks.append(("modest over-limit body rejected", rejected))

    # 7) DecompressedSizeExceeded is a ValueError.
    checks.append(("DecompressedSizeExceeded is ValueError",
                   issubclass(DecompressedSizeExceeded, ValueError)))

    # 8) empty body within the limit round-trips.
    blob, ctype = compression.compress(b"", "zlib")
    out = decompress_bounded(blob, ctype, 64)
    checks.append(("empty body within limit", out == b""))

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"U=0 failed check: {name}")
        return 1

    print(f"U=1 all {len(checks)} utility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
