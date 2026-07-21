We use tablib to let people download their data as a CSV and open it in Excel or Google Sheets. The problem I keep getting support tickets about is that some cells don't show up in the spreadsheet the way they were typed - the spreadsheet app decides a few of them are something other than plain text and renders them differently, so what the user sees in the grid doesn't match what's actually in their data. It's confusing and it makes us look like we're corrupting their export.

I want a dedicated export that's meant specifically for "download this and open it in a spreadsheet" - one where every cell just shows up as the text that was in it, exactly as entered. It should still be a normal CSV (opens by double-click, re-imports fine), it just needs to render predictably cell-for-cell when a human opens it in a spreadsheet app.

I started a module for this and ran out of time. It's in `src/tablib/sheets.py` as `export_sheet_csv(dataset, **kwargs)`, and there's a docstring describing the intent. I need you to implement it.

What I want:

- `export_sheet_csv(dataset, **kwargs)` returns the CSV as a single `str`.
- Write the header row first (if the dataset has headers), then one row per record. You can get the rows out of the dataset the way the existing CSV format does (`dataset._package(dicts=False)` gives you header + data rows).
- Render each cell as its text: `None` should become an empty field, and non-string values (ints, floats) should be stringified.
- Keep it ordinary CSV - build it with the stdlib `csv` module (`csv.writer` on a `StringIO`), and pass `**kwargs` through to the writer so a caller can set things like `delimiter`. The existing `tablib/formats/_csv.py` is a good reference for the shape.
- The whole point is display fidelity: when someone opens this file in Excel / LibreOffice / Google Sheets, each cell should show the value that was in the `Dataset`, not something the app derived from it.

Please also add focused tests in `tests/test_sheets.py` - there's a starter file there already using only `tablib` and the stdlib (no optional format extras), so the tests run without installing xlsx/ods/yaml support. Cover the header row, a few ordinary rows round-tripping back through `csv.reader`, `None` becoming empty, numbers being stringified, and a custom delimiter. The existing test suite should keep passing.
