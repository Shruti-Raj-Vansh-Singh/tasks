from notifier.render import Alert, Team, render_notification


def _alert(**kw):
    base = dict(title="Disk almost full", severity="high", host="web-01",
                owner_email="ops@corp.example",
                owner=Team(name="core", contact="core@corp.example"))
    base.update(kw)
    return Alert(**base)


def test_basic_fields_render():
    tmpl = "[{{ alert.severity | upper }}] {{ alert.title }} on {{ alert.host }}"
    out = render_notification(tmpl, _alert())
    assert out == "[HIGH] Disk almost full on web-01"


def test_plain_text_body():
    tmpl = "Alert for {{ alert.host }}: {{ alert.title }} (contact {{ alert.owner_email }})"
    out = render_notification(tmpl, _alert())
    assert out == "Alert for web-01: Disk almost full (contact ops@corp.example)"


def test_optional_field_with_default():
    tmpl = "{{ alert.title }} -- runbook: {{ alert.runbook_url | default('n/a', true) }}"
    out = render_notification(tmpl, _alert())
    assert out == "Disk almost full -- runbook: n/a"


def test_owning_team_display():
    tmpl = "Owning team: {{ alert.owner.name }} ({{ alert.owner.contact }})"
    out = render_notification(tmpl, _alert())
    assert out == "Owning team: core (core@corp.example)"
