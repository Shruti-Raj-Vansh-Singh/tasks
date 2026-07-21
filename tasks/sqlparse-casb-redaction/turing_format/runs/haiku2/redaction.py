"""Redact literal values from SQL statements.

`redact_literals` rewrites a SQL statement so that its literal *values*
(string and numeric literals) are replaced with a placeholder, while the rest
of the statement is left unchanged. It is meant for safe query logging: you
get the shape of a query for debugging/metrics without recording the actual
data values it carried.

See ``docs/redaction.md`` for the exact behavior this helper must provide.
"""

from __future__ import annotations

import sqlparse
from sqlparse import tokens as T

__all__ = ["redact_literals"]


def redact_literals(sql: str, placeholder: str = "?") -> str:
    """Return ``sql`` with its literal values replaced by ``placeholder``.

    Only literal values are replaced; the rest of the statement (keywords,
    identifiers such as table and column names, functions, operators,
    punctuation, and whitespace) is preserved exactly.

    :param sql: a SQL statement
    :param placeholder: the string to substitute for each literal value
    :returns: the redacted SQL statement
    """
    parsed = sqlparse.parse(sql)[0]
    return _redact_statement(parsed, placeholder)


def _is_literal(token) -> bool:
    """Check if a token is a literal value (string or number)."""
    return token.ttype in (
        T.Literal.String.Single,
        T.Literal.String.Double,
        T.Literal.String.Symbol,
        T.Literal.Number.Integer,
        T.Literal.Number.Float,
        T.Literal.Number.Hexadecimal,
    )


def _redact_statement(parsed, placeholder: str) -> str:
    """Redact a parsed statement by replacing literal values with placeholder."""
    result = []
    for token in parsed.flatten():
        if _is_literal(token):
            result.append(placeholder)
        else:
            result.append(token.value)
    return "".join(result)
