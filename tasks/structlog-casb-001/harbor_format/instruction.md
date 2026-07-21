We're standing up a security audit log for one of our services and I want to use structlog for it. Every auditable action (logins, permission changes, record access) gets logged as one event, and our log pipeline reads the audit file one line per event - SIEM ingestion, grep during incident review, the usual. I started an audit renderer before the weekend and ran out of time; please finish it.

There's a stub `AuditLineRenderer` in `src/structlog/_audit.py` that subclasses nothing special - it's a structlog final processor (it's the last processor in the chain and returns the string the logger writes). It's already exported from `structlog/__init__.py` as `AuditLineRenderer`, and there's a `render_audit_line(event_dict, key_order=None)` convenience wrapper next to it. You just need to fill in the body.

What I want it to produce is a compact, greppable line of space-separated `key=value` pairs, one per field in the event dict, e.g.:

    event=login user=alice outcome=success

Details:

- `render(event_dict)` returns that single string. `render_audit_line(...)` and calling the renderer as a processor (`renderer(logger, name, event_dict)`) should both give the same result.
- `key_order` (a list of keys) controls which fields come first and in what order; any keys not listed come after, in the dict's own order. This lets us always lead with `event` and `user`.
- Values aren't always strings - counts, booleans, ids - so render them with `str()`. Keep it dependency-free; the standard library is all you need.
- It should be usable as the final processor in a normal `structlog.configure(processors=[...])` chain.

Please add focused tests in `tests/test_audit.py` covering the basic `key=value` rendering, that `key_order` is honored with extra keys following, non-string values, and that it works as a final processor in a configured chain. The existing test suite should keep passing.

We log a fair amount of user-supplied data in these events (usernames, resource paths, search terms), so it needs to handle arbitrary field values without falling over. Keep the output on the compact single-line `key=value` shape described above.
