"""Visible tests for install_rpm -- ordinary, well-formed packages only.

Each test builds a small, valid RPM whose payload bytes match the digests its
header declares, and checks that ``install_rpm`` writes the files into
``dest_dir`` and returns a report that lists them. Any correct implementation
passes; nothing here is adversarial.
"""

import gzip
import hashlib
import os
import struct

from rpmkit.install import install_rpm


# --- minimal RPM builder: well-formed packages only (payload == header) -----
def _cpio_member(name, data, mode=0o100644):
    hdr = b"070701"
    fields = [0x1, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(name) + 1, 0]
    hdr += b"".join(b"%08X" % f for f in fields)
    hdr += name.encode() + b"\x00"
    hdr += b"\x00" * ((4 - (len(hdr) % 4)) % 4)
    blob = hdr + data
    blob += b"\x00" * ((4 - (len(blob) % 4)) % 4)
    return blob


def _cpio(members):
    out = b"".join(_cpio_member(n, d) for (n, d) in members)
    out += _cpio_member("TRAILER!!!", b"")
    return out


_TAGS = dict(filesizes=1028, filemodes=1030, filemd5s=1035, dirindexes=1116,
             basenames=1117, dirnames=1118, filedigestalgo=5011)
_I16, _I32, _SARR = 3, 4, 8


def _main_header(entries):
    store = b""
    hdr = []
    for tag, ty, data, count in entries:
        off = len(store)
        hdr.append(struct.pack(b"!iiii", _TAGS[tag], ty, off, count))
        if ty == _I16:
            store += b"".join(struct.pack(b"!H", v) for v in data)
        elif ty == _I32:
            store += b"".join(struct.pack(b"!I", v) for v in data)
        else:
            store += b"".join(s.encode() + b"\x00" for s in data)
    blob = b"\x8e\xad\xe8" + bytes([1]) + b"\x00\x00\x00\x00"
    blob += struct.pack(b"!ii", len(hdr), len(store))
    return blob + b"".join(hdr) + store


def _sig_header():
    return b"\x8e\xad\xe8" + bytes([1]) + b"\x00\x00\x00\x00" + struct.pack(b"!ii", 0, 0)


def _lead():
    return struct.pack(b"!4sBBhh66shh16s", b"\xed\xab\xee\xdb", 3, 0, 0, 1,
                       b"fixture", 0, 5, b"\x00" * 16)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _build(path, files, dirname="/opt/app/"):
    """Write a valid RPM: header digests match payload bytes exactly.

    Every package ships a standard ``LICENSE`` doc, so the header's file tables
    always hold more than one entry -- exactly like the real multi-file RPMs
    these tools unpack.
    """
    files = list(files) + [("LICENSE", b"MIT\n")]
    names = [n for (n, _) in files]
    digs = [_sha(d) for (_, d) in files]
    sizes = [len(d) for (_, d) in files]
    entries = [
        ("basenames", _SARR, names, len(names)),
        ("dirnames", _SARR, [dirname], 1),
        ("dirindexes", _I32, [0] * len(names), len(names)),
        ("filesizes", _I32, sizes, len(names)),
        ("filemodes", _I16, [0o100644] * len(names), len(names)),
        ("filemd5s", _SARR, digs, len(names)),
        ("filedigestalgo", _I32, [8], 1),
    ]
    payload = gzip.compress(_cpio(files))
    raw = _lead() + _sig_header() + b"\x00" * 8 + _main_header(entries) + payload
    with open(path, "wb") as f:
        f.write(raw)
    return str(path)


def _find(root, base):
    for dirpath, _dirs, filenames in os.walk(root):
        if base in filenames:
            return os.path.join(dirpath, base)
    return None


def test_single_file_installed(tmp_path):
    rpm = _build(str(tmp_path / "a.rpm"), [("tool.sh", b"#!/bin/sh\necho hi\n")])
    dest = str(tmp_path / "d1")
    os.makedirs(dest, exist_ok=True)
    install_rpm(rpm, dest)
    p = _find(dest, "tool.sh")
    assert p is not None
    with open(p, "rb") as f:
        assert f.read() == b"#!/bin/sh\necho hi\n"


def test_multiple_files_installed(tmp_path):
    rpm = _build(str(tmp_path / "b.rpm"),
                 [("main.py", b"print(1)\n"), ("data.conf", b"k=v\n")])
    dest = str(tmp_path / "d2")
    os.makedirs(dest, exist_ok=True)
    install_rpm(rpm, dest)
    assert _find(dest, "main.py") is not None
    assert _find(dest, "data.conf") is not None


def test_report_lists_files(tmp_path):
    rpm = _build(str(tmp_path / "c.rpm"), [("app.py", b"Z = 4\n")])
    dest = str(tmp_path / "d3")
    os.makedirs(dest, exist_ok=True)
    report = install_rpm(rpm, dest)
    assert "app.py" in repr(report)


def test_report_has_digest_and_size(tmp_path):
    data = b"WORD = 42\n"
    rpm = _build(str(tmp_path / "d.rpm"), [("conf.py", data)])
    dest = str(tmp_path / "d4")
    os.makedirs(dest, exist_ok=True)
    report = install_rpm(rpm, dest)
    text = repr(report)
    assert str(len(data)) in text          # size present somewhere
    assert _sha(data)[:16] in text          # digest present somewhere


def test_bytes_written_verbatim(tmp_path):
    body = b"line1\nline2\nline3\n"
    rpm = _build(str(tmp_path / "e.rpm"), [("payload.txt", body)])
    dest = str(tmp_path / "d5")
    os.makedirs(dest, exist_ok=True)
    install_rpm(rpm, dest)
    p = _find(dest, "payload.txt")
    assert p is not None
    with open(p, "rb") as f:
        assert f.read() == body
