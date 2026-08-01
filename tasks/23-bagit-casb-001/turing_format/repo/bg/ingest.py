# -*- coding: utf-8 -*-
"""Ingest a received BagIt package into a catalog record.

See docs/ingesting.rst and INGEST_TASK.md.
"""

from __future__ import annotations


def ingest_bag(bag_dir):
    """Load the BagIt package at *bag_dir* and return a catalog record.

    :param bag_dir: path to a directory holding a received BagIt package.
    :returns: a dict with ``"metadata"`` (the bag-info tags) and ``"payload"``
        (a list of the payload files, each with its ``path``, ``hash``, and
        ``size``).
    """
    raise NotImplementedError("ingest_bag is not implemented yet")
