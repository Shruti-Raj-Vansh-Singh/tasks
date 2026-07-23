"""Visible tests for install_wheel -- ordinary, well-formed wheels only.

Each test builds a small, valid wheel whose files match its ``RECORD`` manifest
and checks that ``install_wheel`` writes the files into the ``purelib`` scheme
directory and returns a report that lists them. Any correct implementation
passes; nothing here is adversarial.
"""

import base64
import hashlib
import os
import zipfile

import pytest

from iw.apply import install_wheel


def _hash(data):
    d = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(d).rstrip(b"=").decode()


def _build(path, dist, files):
    """Write a valid wheel containing *files* ({archive_path: bytes})."""
    di = f"{dist}-1.0.dist-info"
    meta = f"Metadata-Version: 2.1\nName: {dist}\nVersion: 1.0\n".encode()
    wheel = (
        "Wheel-Version: 1.0\nGenerator: t\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
    ).encode()
    rows = [f"{p},{_hash(b)},{len(b)}" for p, b in files.items()]
    rows.append(f"{di}/METADATA,{_hash(meta)},{len(meta)}")
    rows.append(f"{di}/WHEEL,{_hash(wheel)},{len(wheel)}")
    rows.append(f"{di}/RECORD,,")
    rec = ("\n".join(rows) + "\n").encode()
    with zipfile.ZipFile(path, "w") as zf:
        for p, b in files.items():
            zf.writestr(p, b)
        zf.writestr(f"{di}/METADATA", meta)
        zf.writestr(f"{di}/WHEEL", wheel)
        zf.writestr(f"{di}/RECORD", rec)
    return str(path)


def _schemes(root):
    d = {k: os.path.join(root, k) for k in
         ("purelib", "platlib", "headers", "scripts", "data")}
    for p in d.values():
        os.makedirs(p, exist_ok=True)
    return d


def test_single_file_installed(tmp_path):
    whl = _build(tmp_path / "a-1.0-py3-none-any.whl", "a",
                 {"a/__init__.py": b"X = 1\n"})
    dirs = _schemes(str(tmp_path / "t"))
    install_wheel(whl, dirs)
    with open(os.path.join(dirs["purelib"], "a", "__init__.py"), "rb") as f:
        assert f.read() == b"X = 1\n"


def test_multiple_files_installed(tmp_path):
    whl = _build(tmp_path / "b-1.0-py3-none-any.whl", "b",
                 {"b/__init__.py": b"Y = 2\n", "b/util.py": b"def g():\n    return 3\n"})
    dirs = _schemes(str(tmp_path / "t"))
    install_wheel(whl, dirs)
    base = os.path.join(dirs["purelib"], "b")
    assert os.path.exists(os.path.join(base, "__init__.py"))
    assert os.path.exists(os.path.join(base, "util.py"))


def test_report_lists_files(tmp_path):
    whl = _build(tmp_path / "c-1.0-py3-none-any.whl", "c",
                 {"c/__init__.py": b"Z = 4\n"})
    dirs = _schemes(str(tmp_path / "t"))
    report = install_wheel(whl, dirs)
    text = repr(report)
    assert "c/__init__.py" in text


def test_report_has_hash_and_size(tmp_path):
    data = b"WORD = 42\n"
    whl = _build(tmp_path / "d-1.0-py3-none-any.whl", "d",
                 {"d/__init__.py": data})
    dirs = _schemes(str(tmp_path / "t"))
    report = install_wheel(whl, dirs)
    text = repr(report)
    assert str(len(data)) in text  # size present somewhere
    assert "sha256=" in text       # hash present somewhere


def test_nested_package(tmp_path):
    whl = _build(tmp_path / "e-1.0-py3-none-any.whl", "e",
                 {"e/__init__.py": b"", "e/sub/__init__.py": b"N = 1\n"})
    dirs = _schemes(str(tmp_path / "t"))
    install_wheel(whl, dirs)
    assert os.path.exists(os.path.join(dirs["purelib"], "e", "sub", "__init__.py"))
