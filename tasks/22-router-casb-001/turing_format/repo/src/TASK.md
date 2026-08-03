# Implement operator-authored alert routing rules

When an alert fires we have to decide what to label it and which queue it lands
in. That logic used to live in a big if/else in our code and it was a constant
source of tickets - every team wanted their alerts routed a little differently
and we were the bottleneck. So we pushed it into the product: each team now
writes their own routing rules in the web UI, as small one-line expressions,
and we evaluate them when an alert comes in. We went with plain Python
expression syntax because it's what people already reach for, e.g.:

    record.owner.name if record.severity == "high" else "triage"

Most rules are simple comparisons like that, but people do get creative -
string checks on the host, fallbacks with `or`, that kind of thing - so
whatever a team saved needs to just work.

Right now `router/rules.py` has the `Alert` record (and the `Team` it belongs
to) and an `evaluate_rule(rule_source, record)` stub that just raises
`NotImplementedError`. I got the scaffolding in place but didn't get to the
implementation - can you take it from here?

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
