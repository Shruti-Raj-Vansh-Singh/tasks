# -*- coding: utf-8 -*-
"""Test helper: build a well-formed BagIt package on disk."""

from __future__ import annotations

import os

import bagit


def make_well_formed_bag(root, files, info=None, algorithms=None):
    """Create a valid bag under *root* containing *files*.

    :param root: directory to turn into a bag (created if missing).
    :param files: dict mapping a relative payload path (posix, no ``data/``
        prefix) to its bytes.
    :param info: optional bag-info tags.
    :param algorithms: manifest algorithms (default ``["sha256"]``).
    """
    os.makedirs(root, exist_ok=True)
    for rel, data in files.items():
        dest = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
    bag = bagit.make_bag(
        root, info or {}, checksums=algorithms or ["sha256"]
    )
    return bag
