# Render operator-authored notification templates

Our alerting service fans out a notification whenever an alert fires - e-mail
and Slack, mostly. For a long time the wording of those was hard-coded and
nobody was happy with it: every team wanted theirs to read a little
differently, so we moved it into the product. Each team now writes their own
subject line and body in the web UI and we render that against the alert that
fired. They're written in Jinja2 (that's what people already knew), and they
reference the alert directly, for example:

    [{{ alert.severity | upper }}] {{ alert.title }} on {{ alert.host }}

Some teams keep it to a single line; others build out longer bodies with
conditionals and fallbacks, so the renderer needs to cope with whatever a team
has put together.

Right now `notifier/render.py` has the `Alert` record (and the `Team` it belongs
to) and a `render_notification(template_source, alert)` stub that just raises
`NotImplementedError`. I got the surrounding pieces in place before I got pulled
onto something else - could you fill in the implementation?

## What `render_notification` should do

- Take `template_source` (the Jinja2 template text the operator saved for their
  team) and the `alert` record that fired.
- Render the template against the alert and return the resulting notification
  text - that's what we hand off to the transport layer.
- Operators expect the usual Jinja2 conveniences (filters like `upper`,
  `default`, conditionals) to work in their templates, and to be able to
  reference the owning team (e.g. `{{ alert.owner.name }}`).

## Checking your work

```
python -m pytest notifier_tests/test_render.py -q
```

`jinja2` is installed. Thanks!
