"""Spreadsheet-friendly CSV export for :class:`tablib.Dataset`.

The built-in ``csv`` export (:mod:`tablib.formats._csv`) is a faithful RFC 4180
serialization: it is meant to round-trip back through a CSV reader. When the
file is instead opened directly in a desktop spreadsheet application (Excel,
LibreOffice Calc, Google Sheets), some cells do not display as the text that
was entered - the application interprets them instead of showing them - so the
sheet a person sees does not match the data in the ``Dataset``.

This module adds :func:`export_sheet_csv`, a CSV exporter tuned so that every
cell shows up in a spreadsheet application as the literal text it held in the
``Dataset``. The output is still ordinary CSV (same delimiter/quoting rules), so
it opens by double-click and re-imports cleanly; it just renders predictably
cell-for-cell when a human opens it.

Example::

    import tablib
    from tablib.sheets import export_sheet_csv

    ds = tablib.Dataset()
    ds.headers = ["item", "qty"]
    ds.append(["widgets", 12])

    csv_text = export_sheet_csv(ds)
    # -> 'item,qty\\r\\nwidgets,12\\r\\n'
"""
from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from .core import Dataset


def export_sheet_csv(dataset: "Dataset", **kwargs: t.Any) -> str:
    """Return ``dataset`` as CSV text that displays cell-for-cell in a
    spreadsheet application.

    Args:
        dataset: The :class:`tablib.Dataset` to serialize. Its header row (if
            any) is written first, followed by each data row.
        **kwargs: Passed through to the underlying :class:`csv.writer` (e.g.
            ``delimiter``), so the caller can match whatever dialect they use
            elsewhere.

    Returns:
        The CSV document as a single ``str``. Each cell is rendered as its
        text (``None`` becomes an empty field) and appears in a spreadsheet app
        as the value that was stored in the ``Dataset``.
    """
    raise NotImplementedError("export_sheet_csv is not implemented yet")
