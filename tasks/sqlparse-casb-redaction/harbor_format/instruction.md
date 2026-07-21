We log slow queries in our services, but we can't keep the raw SQL around --
it carries customer data (emails, names, ids) straight into our logs. We'd
like to log a redacted form instead: the same query with its literal *values*
blanked out, so we can still see the shape of a query for debugging and
grouping without storing the actual data.

I've scaffolded a helper in `sqlparse/redaction.py`:
`redact_literals(sql, placeholder="?")`. The body currently raises
`NotImplementedError` -- please implement it.

It should take a SQL statement and return the same statement with its literal
values (the string and numeric values a query carries) replaced by
`placeholder`, leaving the rest of the statement as it was so the query is
still recognizable. For example, a `WHERE email = 'a@b.com' AND age = 42`
should come back as `WHERE email = ? AND age = ?`.

There's a short design note at `docs/redaction.md` describing exactly what
counts as a value to redact and what should be left as-is. We're already
depending on `sqlparse` here, so use what the library gives you rather than
pulling in anything new.

Please implement `redact_literals`, add a few focused tests, and keep the
existing suite passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
