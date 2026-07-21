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


def _is_value(ttype) -> bool:
    """Return whether a token type denotes a literal *value* to redact.

    Numeric and string literals are values. Double-quoted names tokenize as
    ``String.Symbol``; those are quoted identifiers, not values, so they are
    excluded even though they live under ``Literal``.
    """
    return ttype in T.Literal and ttype not in T.String.Symbol


def redact_literals(sql: str, placeholder: str = "?") -> str:
    """Return ``sql`` with its literal values replaced by ``placeholder``.

    Only literal values are replaced; the rest of the statement (keywords,
    identifiers such as table and column names, functions, operators,
    punctuation, and whitespace) is preserved exactly.

    :param sql: a SQL statement
    :param placeholder: the string to substitute for each literal value
    :returns: the redacted SQL statement
    """
    return "".join(
        placeholder if _is_value(token.ttype) else token.value
        for statement in sqlparse.parse(sql)
        for token in statement.flatten()
    )
