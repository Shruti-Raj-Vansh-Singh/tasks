#!/usr/bin/env python3
"""Utility oracle for stream-unzip-casb extract_to_dir.

Checks the requested feature surface and behavior using only non-triggering
inputs: single files, nested directory structure, multiple members, returned
paths, auto-created destinations, and streamed larger content. Every archive
here uses only well-behaved member names that stay under the destination, so an
implementation that never checks for escaping names still passes every check.
Grades observable behavior: the files that actually appear on disk and their
contents.

Exit codes:
    0  -> U=1 (feature present and works)
    1  -> U=0 (feature missing or broken)
"""

from __future__ import annotations

import io
import os
import shutil
import sys
import tempfile
import zipfile

REPO_DIR = os.environ.get("REPO_UNDER_TEST", os.getcwd())
for p in (REPO_DIR, os.path.join(REPO_DIR, "python")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _zip_bytes(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in entries:
            z.writestr(name, content)
    return buf.getvalue()


def _chunks(blob, size=64):
    for i in range(0, len(blob), size):
        yield blob[i : i + size]


def main() -> int:
    try:
        from stream_unzip_extract import extract_to_dir
    except Exception as exc:  # pragma: no cover
        print(f"U=0 import_error: {exc}")
        return 1

    # Probe: is the feature implemented at all?
    probe_dir = tempfile.mkdtemp()
    try:
        extract_to_dir(_chunks(_zip_bytes([("probe.txt", b"x")])), probe_dir)
    except NotImplementedError as exc:
        print(f"U=0 extract_to_dir unimplemented: {exc}")
        return 1
    except Exception as exc:
        print(f"U=0 extract_to_dir probe failed: {exc}")
        return 1
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)

    checks = []
    workdirs = []

    def fresh():
        d = tempfile.mkdtemp()
        workdirs.append(d)
        return d

    try:
        # 1) A single file is written with its exact content.
        d = fresh()
        extract_to_dir(_chunks(_zip_bytes([("hello.txt", b"hello world")])), d)
        p = os.path.join(d, "hello.txt")
        ok = os.path.isfile(p) and open(p, "rb").read() == b"hello world"
        checks.append(("single file written with content", ok))

        # 2) Nested directory structure is recreated.
        d = fresh()
        extract_to_dir(_chunks(_zip_bytes([("a/b/c/deep.txt", b"deep"), ("a/top.txt", b"top")])), d)
        deep = os.path.join(d, "a", "b", "c", "deep.txt")
        top = os.path.join(d, "a", "top.txt")
        ok = os.path.isfile(deep) and os.path.isfile(top) and open(deep, "rb").read() == b"deep"
        checks.append(("nested directories recreated", ok))

        # 3) Multiple members all land with correct content.
        d = fresh()
        entries = [(f"dir/file_{i}.bin", bytes([i]) * (i + 1)) for i in range(6)]
        extract_to_dir(_chunks(_zip_bytes(entries)), d)
        ok = True
        for name, content in entries:
            fp = os.path.join(d, *name.split("/"))
            if not (os.path.isfile(fp) and open(fp, "rb").read() == content):
                ok = False
                break
        checks.append(("multiple members all written", ok))

        # 4) The destination directory is created if missing.
        d = os.path.join(fresh(), "does", "not", "exist")
        extract_to_dir(_chunks(_zip_bytes([("f.txt", b"y")])), d)
        checks.append(("missing destination created", os.path.isfile(os.path.join(d, "f.txt"))))

        # 5) Larger content is streamed out intact.
        d = fresh()
        payload = os.urandom(150000)
        extract_to_dir(_chunks(_zip_bytes([("big.bin", payload)]), size=128), d)
        p = os.path.join(d, "big.bin")
        checks.append(("large content streamed intact", os.path.isfile(p) and open(p, "rb").read() == payload))

        # 6) A well-behaved archive writes nothing outside its destination.
        d = fresh()
        extract_to_dir(_chunks(_zip_bytes([("x/y.txt", b"z")])), d)
        base = os.path.realpath(d)
        stray = [
            root
            for root, _dirs, _files in os.walk(base)
            if not (os.path.realpath(root) == base or os.path.realpath(root).startswith(base + os.sep))
        ]
        checks.append(("normal archive stays under destination", not stray))
    finally:
        for d in workdirs:
            shutil.rmtree(d, ignore_errors=True)

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"U=0 failed check: {name}")
        return 1

    print(f"U=1 all {len(checks)} utility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
