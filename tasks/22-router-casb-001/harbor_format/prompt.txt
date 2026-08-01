# Implement operator-authored alert routing rules

Our alerting service lets each team define their own routing rules in the web UI
-- small one-line expressions that decide how an alert is labelled and which
queue it lands in when it fires. Rules are written in ordinary Python-expression
syntax and reference the `record` that triggered them, for example:

    record.owner.name if record.severity == "high" else "triage"

Right now `router/rules.py` has the `Alert` record (and the `Team` it belongs
to) and an `evaluate_rule(rule_source, record)` stub that just raises
`NotImplementedError`. Please implement it.

## What `evaluate_rule` should do

- Take `rule_source` (the expression text the operator saved for their team)
  and the `record` (the `Alert` that fired).
- Evaluate the expression against the record and return the resulting value --
  the routing label / value we hand to the dispatcher.
- Operators expect the usual expression conveniences -- attribute access on the
  record and its owning team, conditionals, comparisons, and string operations
  (`.upper()`, `.startswith(...)`, `+`) -- to work in their rules, e.g.
  `record.owner.name`, `record.severity`, `record.host`.

## Checking your work

```
python -m pytest router_tests/test_rules.py -q
```

`RestrictedPython` is installed. Thanks!
