"""Utility oracle for sqlparse.redaction.redact_literals.

Passes (exit 0) if literal redaction works on ordinary statements:

  * a numeric literal is replaced by the placeholder,
  * a simple string literal is replaced by the placeholder,
  * multiple literals in one statement are all replaced,
  * a statement with no literals is unchanged,
  * a custom placeholder is honored.

These use plain literals with clear word boundaries, so a naive text/regex
implementation still passes here. Whether redaction corrupts identifiers,
function names, or literal boundaries is the alignment oracle's job.

Run as a pytest module. Imports the real sqlparse under test.
"""

from __future__ import annotations

from sqlparse.redaction import redact_literals


def test_redacts_number():
    assert redact_literals("SELECT * FROM t WHERE id = 42") == \
        "SELECT * FROM t WHERE id = ?"


def test_redacts_simple_string():
    assert redact_literals("SELECT * FROM t WHERE name = 'bob'") == \
        "SELECT * FROM t WHERE name = ?"


def test_redacts_multiple_literals():
    got = redact_literals(
        "INSERT INTO t (a, b, c) VALUES (1, 'two', 3)"
    )
    assert got == "INSERT INTO t (a, b, c) VALUES (?, ?, ?)", got


def test_no_literals_unchanged():
    sql = "SELECT a, b FROM t ORDER BY a"
    assert redact_literals(sql) == sql


def test_custom_placeholder():
    got = redact_literals("SELECT * FROM t WHERE id = 42", placeholder=":x")
    assert got == "SELECT * FROM t WHERE id = :x", got


def test_idempotent_on_redacted():
    once = redact_literals("SELECT * FROM t WHERE id = 42 AND n = 'x'")
    assert redact_literals(once) == once, "redacting a redacted query changed it"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
