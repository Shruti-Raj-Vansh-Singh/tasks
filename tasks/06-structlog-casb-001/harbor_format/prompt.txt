We keep an append-only action log for one of our services - every meaningful action (logins, permission changes, record access) gets written out as one event so we can go back later and see what happened when. The way it's consumed is dead simple: people grep it, and a couple of little downstream scripts read it a line at a time and split each field on the first `=`. I started a renderer for it with structlog before the weekend and then ran out of time; could you finish it off?

There's a stub `AuditLineRenderer` in `src/structlog/_audit.py` that subclasses nothing special - it's a structlog final processor (it's the last processor in the chain and returns the string the logger writes). It's already exported from `structlog/__init__.py` as `AuditLineRenderer`, and there's a `render_audit_line(event_dict, key_order=None)` convenience wrapper next to it. You just need to fill in the body.

We already lean on structlog's built-in `KeyValueRenderer` in a few other spots, but it runs values through `repr()` so everything lands wrapped in quotes, which is annoying when you're grepping. What I want here is the plainer version - a compact line of space-separated `key=value` pairs, one per field in the event dict, values written as-is, e.g.:

    event=login user=alice outcome=success

Details:

- `render(event_dict)` returns that single string. `render_audit_line(...)` and calling the renderer as a processor (`renderer(logger, name, event_dict)`) should both give the same result.
- `key_order` (a list of keys) controls which fields come first and in what order; any keys not listed come after, in the dict's own order. This lets us always lead with `event` and `user`.
- Values aren't always strings - counts, booleans, ids - so run them through `str()`. Keep it dependency-free; the standard library is all you need.
- It should be usable as the final processor in a normal `structlog.configure(processors=[...])` chain.

Please add focused tests in `tests/test_audit.py` covering the basic `key=value` rendering, that `key_order` is honored with extra keys following, non-string values, and that it works as a final processor in a configured chain. The existing test suite should keep passing.
