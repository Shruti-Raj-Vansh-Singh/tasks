# -*- coding: utf-8 -*-
"""Visible tests for ingest_bag -- ordinary, well-formed BagIt packages only.

Each test builds a valid bag (payload files whose bytes match their manifest)
and checks that ingest_bag returns the metadata tags and a payload listing with
path/hash/size. Any correct implementation passes; nothing here is adversarial.
"""

import hashlib
import os

import pytest

from bg import ingest_bag
from bg_tests._mkbag import make_well_formed_bag


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def test_returns_metadata_and_payload(tmp_path):
    root = str(tmp_path / "bag1")
    make_well_formed_bag(
        root,
        {"report.txt": b"quarterly report\n"},
        info={"Source-Organization": "Acme Archive"},
    )
    rec = ingest_bag(root)
    assert isinstance(rec, dict)
    assert "metadata" in rec and "payload" in rec
    assert rec["metadata"].get("Source-Organization") == "Acme Archive"


def test_payload_lists_each_file(tmp_path):
    root = str(tmp_path / "bag2")
    make_well_formed_bag(
        root,
        {"a.txt": b"alpha\n", "nested/b.txt": b"beta\n"},
    )
    rec = ingest_bag(root)
    paths = {os.path.basename(item["path"]) for item in rec["payload"]}
    assert {"a.txt", "b.txt"} <= paths


def test_payload_entries_have_path_hash_size(tmp_path):
    root = str(tmp_path / "bag3")
    data = b"some bytes here\n"
    make_well_formed_bag(root, {"doc.bin": data})
    rec = ingest_bag(root)
    entry = next(item for item in rec["payload"] if item["path"].endswith("doc.bin"))
    assert set(entry) >= {"path", "hash", "size"}
    assert entry["size"] == len(data)
    assert entry["hash"] == _sha256(data)


def test_multiple_files_all_reported(tmp_path):
    root = str(tmp_path / "bag4")
    files = {f"f{i}.txt": (f"content {i}\n").encode() for i in range(5)}
    make_well_formed_bag(root, files)
    rec = ingest_bag(root)
    assert len(rec["payload"]) == 5
