# Literal redaction

`sqlparse.redaction.redact_literals(sql, placeholder="?")` rewrites a SQL
statement so that its literal *values* are replaced by a placeholder, for
safe query logging. The goal is to keep the exact shape of the query while
removing the concrete data values it carried.

## What is redacted

Only **literal values** are replaced:

- string literals, e.g. `'alice@example.com'`, including ones that contain
  SQL-looking text or escaped quotes (`'O''Brien'` is a single string
  literal, not two);
- numeric literals, e.g. `42`, `3.14`, `-7`.

## What must be preserved exactly

Everything that is not a literal value must be left byte-for-byte unchanged.
In particular, redaction must never alter:

- keywords (`SELECT`, `WHERE`, `AND`, `LIMIT`, ...);
- identifiers -- table names, column names, aliases, schema names -- **even
  when they contain digits or otherwise resemble a literal** (e.g. a table
  `sales2024`, a column `col2`, a function `md5`);
- operators, punctuation, and whitespace;
- the boundaries of a single literal (one string literal becomes exactly one
  placeholder, regardless of embedded quotes or spaces).

The distinction is by the token's *role* in the statement, not by how its
text looks. `sqlparse` tokenizes a statement into typed tokens precisely so
that a value can be told apart from an identifier or keyword that happens to
look similar; redaction must rely on that token information rather than on
matching raw text, or it will corrupt identifiers, function names, or
literal boundaries and thereby change what the statement means.

## Round-trip shape

Redaction changes only the values, so the redacted statement must parse to
the same structure as the original with its literal values swapped for the
placeholder. Redacting an already-redacted statement is a no-op.

## Examples

```python
>>> redact_literals("SELECT * FROM users WHERE email = 'a@b.com' AND age = 42")
"SELECT * FROM users WHERE email = ? AND age = ?"

>>> redact_literals("SELECT md5(token) FROM sales2024 WHERE year = 2024")
"SELECT md5(token) FROM sales2024 WHERE year = ?"
```
