#!/usr/bin/env python
"""Tests for tablib.sheets.export_sheet_csv.

These use only tablib + the standard library so they run without the optional
format extras (xlsx/ods/yaml/...). They cover the export's behavior on ordinary
values; a spreadsheet reader should get back exactly what was put in.
"""
import csv
import io
import unittest

import tablib
from tablib.sheets import export_sheet_csv


def _rows(csv_text):
    return list(csv.reader(io.StringIO(csv_text)))


class ExportSheetCSVTests(unittest.TestCase):
    def _dataset(self, headers, rows):
        ds = tablib.Dataset()
        if headers is not None:
            ds.headers = headers
        for r in rows:
            ds.append(r)
        return ds

    def test_headers_and_rows_present(self):
        ds = self._dataset(["item", "qty"], [["widgets", "12"], ["gadgets", "3"]])
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[0], ["item", "qty"])
        self.assertEqual(rows[1], ["widgets", "12"])
        self.assertEqual(rows[2], ["gadgets", "3"])

    def test_roundtrips_through_csv_reader(self):
        ds = self._dataset(["a", "b"], [["1", "2"], ["3", "4"]])
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows, [["a", "b"], ["1", "2"], ["3", "4"]])

    def test_plain_values_are_unchanged(self):
        # Ordinary text that does not begin with a special character must be
        # exported exactly as entered - not truncated or stripped.
        ds = self._dataset(
            ["expr", "lang", "path"],
            [["2+2=4", "C++", "a-b-c"]],
        )
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[1], ["2+2=4", "C++", "a-b-c"])

    def test_email_and_interior_symbols_preserved(self):
        ds = self._dataset(
            ["email", "note"],
            [["user@example.com", "3=1+2 in disguise"]],
        )
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[1], ["user@example.com", "3=1+2 in disguise"])

    def test_none_becomes_empty_field(self):
        ds = self._dataset(["a", "b"], [["x", None]])
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[1], ["x", ""])

    def test_numbers_are_stringified(self):
        ds = self._dataset(["n"], [[42], [3.5]])
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[1], ["42"])
        self.assertEqual(rows[2], ["3.5"])

    def test_unicode_preserved(self):
        ds = self._dataset(["name"], [["café"], ["日本語"]])
        rows = _rows(export_sheet_csv(ds))
        self.assertEqual(rows[1], ["café"])
        self.assertEqual(rows[2], ["日本語"])

    def test_values_with_commas_are_quoted_and_roundtrip(self):
        ds = self._dataset(["addr"], [["1, Main St"]])
        text = export_sheet_csv(ds)
        self.assertEqual(_rows(text)[1], ["1, Main St"])

    def test_custom_delimiter(self):
        ds = self._dataset(["a", "b"], [["1", "2"]])
        text = export_sheet_csv(ds, delimiter=";")
        rows = list(csv.reader(io.StringIO(text), delimiter=";"))
        self.assertEqual(rows[0], ["a", "b"])
        self.assertEqual(rows[1], ["1", "2"])

    def test_returns_str(self):
        ds = self._dataset(["a"], [["1"]])
        self.assertIsInstance(export_sheet_csv(ds), str)

    def test_empty_dataset_has_no_rows(self):
        ds = tablib.Dataset()
        text = export_sheet_csv(ds)
        self.assertEqual([r for r in _rows(text) if r], [])


if __name__ == "__main__":
    unittest.main()
