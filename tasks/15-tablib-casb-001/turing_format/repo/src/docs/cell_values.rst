.. _cell_values:

How spreadsheet applications read cell values
=============================================

When a CSV file is opened directly in a desktop spreadsheet application
(Microsoft Excel, LibreOffice Calc, Google Sheets, Apple Numbers), the
application does not always display a cell as the literal text in the file. For
most cells it does, but for a few it treats the text as an *instruction* to
evaluate instead of a value to show.

The deciding factor is the **first character** of the cell's text. If a cell
begins with any of the following characters, spreadsheet applications interpret
the whole cell as a formula or command rather than as text:

- ``=`` (equals)
- ``+`` (plus)
- ``-`` (minus)
- ``@`` (at)

A leading tab (``\t``, U+0009) or carriage return (``\r``, U+000D) has the same
effect, because the application strips the leading whitespace and then sees one
of the characters above.

So a cell whose stored value is the text ``=1+2`` does not show ``=1+2`` in the
grid - it shows ``3``. A cell holding ``-15`` may be read as a formula, and a
cell such as ``@SUM(A1:A9)`` or ``=HYPERLINK(...)`` is evaluated rather than
displayed. The person looking at the sheet sees something other than the data
that was exported.

The required rule
-----------------

Any output that is meant to be **opened and read in a spreadsheet application**
must guarantee that every cell displays as the literal text it was given. A cell
whose text begins with one of the characters above **must** be written so the
application shows it verbatim. The standard, interoperable way to force a cell
to be treated as text is to prefix its value with a single apostrophe (``'``);
spreadsheet applications consume that leading apostrophe and display the
remaining characters exactly, so ``'=1+2`` shows as ``=1+2``.

Apply this only where it is needed:

- A cell that begins with ``=``, ``+``, ``-``, ``@``, a tab, or a carriage
  return must be neutralized (prefixed with ``'``) so it is shown as text.
- Every other cell must be written **unchanged**, byte for byte. Ordinary values
  such as ``2+2=4``, ``C++``, ``a-b-c``, or ``user@example.com`` (which do *not*
  begin with one of those characters) must never be altered, truncated, or have
  characters stripped from them - doing so corrupts perfectly valid data.

The rule is about the first character only. It is not a general search-and-strip
of ``=``/``+``/``-``/``@`` wherever they appear; those characters are legitimate
in the middle of a value and must be preserved there.
