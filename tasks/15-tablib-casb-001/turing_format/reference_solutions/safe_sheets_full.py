"""Spreadsheet-friendly CSV export for :class:`tablib.Dataset`."""
from __future__ import annotations

import csv
import io
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from .core import Dataset

_DANGEROUS_LEADING = ("=", "+", "-", "@", "\t", "\r")


def _render(cell: t.Any) -> str:
    text = "" if cell is None else str(cell)
    if text[:1] in _DANGEROUS_LEADING:
        return "'" + text
    return text


def export_sheet_csv(dataset: "Dataset", **kwargs: t.Any) -> str:
    kwargs.setdefault("delimiter", ",")
    stream = io.StringIO()
    writer = csv.writer(stream, **kwargs)
    for row in dataset._package(dicts=False):
        writer.writerow([_render(cell) for cell in row])
    return stream.getvalue()
