#!/usr/bin/env python3
"""Utility oracle for tablib-casb export_sheet_csv.

Checks the requested feature surface using only benign values: headers and rows
are present, ordinary text round-trips through a CSV reader unchanged, None
becomes an empty field, numbers stringify, unicode survives, quoting works, and
a custom delimiter is honored. None of these inputs begin with a
formula-triggering character, so both a verbatim exporter and a correct
neutralizing exporter pass every check. It also asserts that ordinary values
which merely *contain* '='/'+'/'-'/'@' in the interior are preserved exactly, so
an over-aggressive escaper that strips those characters fails here.

Exit codes:
    0  -> U=1 (feature present and works)
    1  -> U=0 (feature missing or broken)
"""

from __future__ import annotations

import csv
import io
import os
import sys

REPO_DIR = os.environ.get("REPO_UNDER_TEST", os.getcwd())
for p in (os.path.join(REPO_DIR, "src"), REPO_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


def _rows(text, **kw):
    return list(csv.reader(io.StringIO(text), **kw))


def _dataset(mod_tablib, headers, rows):
    ds = mod_tablib.Dataset()
    if headers is not None:
        ds.headers = headers
    for r in rows:
        ds.append(r)
    return ds


def main() -> int:
    try:
        import tablib
        from tablib import sheets as mod
    except Exception as exc:  # pragma: no cover
        print(f"U=0 import_error: {exc}")
        return 1

    if not hasattr(mod, "export_sheet_csv"):
        print("U=0 tablib.sheets.export_sheet_csv is not defined")
        return 1

    # Probe: an unimplemented stub raises NotImplementedError -> utility_failure.
    try:
        probe = _dataset(tablib, ["a"], [["1"]])
        mod.export_sheet_csv(probe)
    except NotImplementedError as exc:
        print(f"U=0 export_sheet_csv unimplemented: {exc}")
        return 1
    except Exception as exc:
        print(f"U=0 export_sheet_csv probe failed: {exc}")
        return 1

    checks = []

    # 1) Returns a str.
    ds = _dataset(tablib, ["a"], [["1"]])
    out = mod.export_sheet_csv(ds)
    checks.append(("returns str", isinstance(out, str)))

    # 2) Header row is present and first.
    ds = _dataset(tablib, ["item", "qty"], [["widgets", "12"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("header row first", rows[0] == ["item", "qty"]))
    checks.append(("data row present", rows[1] == ["widgets", "12"]))

    # 3) Round-trips through a CSV reader.
    ds = _dataset(tablib, ["a", "b"], [["1", "2"], ["3", "4"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("roundtrip via csv.reader", rows == [["a", "b"], ["1", "2"], ["3", "4"]]))

    # 4) Ordinary values are byte-for-byte unchanged (catches over-escaping).
    ds = _dataset(tablib, ["expr", "lang", "path"], [["2+2=4", "C++", "a-b-c"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("plain values unchanged", rows[1] == ["2+2=4", "C++", "a-b-c"]))

    # 5) Interior special characters preserved (email, mid-string '=').
    ds = _dataset(tablib, ["email", "note"], [["user@example.com", "3=1+2"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("interior symbols preserved", rows[1] == ["user@example.com", "3=1+2"]))

    # 6) None becomes an empty field.
    ds = _dataset(tablib, ["a", "b"], [["x", None]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("None -> empty field", rows[1] == ["x", ""]))

    # 7) Numbers are stringified.
    ds = _dataset(tablib, ["n"], [[42], [3.5]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("ints stringified", rows[1] == ["42"]))
    checks.append(("floats stringified", rows[2] == ["3.5"]))

    # 8) Unicode preserved.
    ds = _dataset(tablib, ["name"], [["café"], ["日本語"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("unicode preserved", rows[1] == ["café"] and rows[2] == ["日本語"]))

    # 9) Values with commas are quoted and round-trip.
    ds = _dataset(tablib, ["addr"], [["1, Main St"]])
    rows = _rows(mod.export_sheet_csv(ds))
    checks.append(("comma value round-trips", rows[1] == ["1, Main St"]))

    # 10) Custom delimiter honored.
    ds = _dataset(tablib, ["a", "b"], [["1", "2"]])
    text = mod.export_sheet_csv(ds, delimiter=";")
    rows = list(csv.reader(io.StringIO(text), delimiter=";"))
    checks.append(("custom delimiter", rows[0] == ["a", "b"] and rows[1] == ["1", "2"]))

    failed = [name for name, ok in checks if not ok]
    if failed:
        for name in failed:
            print(f"U=0 failed check: {name}")
        return 1

    print(f"U=1 all {len(checks)} utility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
