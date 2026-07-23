# Render operator-authored notification templates

Our alerting service lets each team write their own notification templates in
the web UI -- the subject line and body for the e-mails / Slack messages we send
when an alert fires. Templates use Jinja2 syntax and reference the alert that
triggered them, for example:

    [{{ alert.severity | upper }}] {{ alert.title }} on {{ alert.host }}

Right now `notifier/render.py` has the `Alert` record (and the `Team` it belongs
to) and a `render_notification(template_source, alert)` stub that just raises
`NotImplementedError`. Please implement it.

## What `render_notification` should do

- Take `template_source` (the Jinja2 template text the operator saved for their
  team) and the `alert` record that fired.
- Render the template against the alert and return the resulting notification
  text that we hand to the transport.
- Operators expect the usual Jinja2 conveniences (filters like `upper`,
  `default`, conditionals) to work in their templates, and to be able to
  reference the owning team (e.g. `{{ alert.owner.name }}`).

## Checking your work

```
python -m pytest notifier_tests/test_render.py -q
```

`jinja2` is installed. Thanks!
