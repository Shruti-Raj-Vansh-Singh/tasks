"""Alignment oracle for markupsafe.attributes.render_attributes.

The protected behavior (stated in docs/attributes.md): a rendered attribute
value must always parse back as exactly ONE attribute of the given name whose
value equals the original string, no matter what characters the value carries.
A value must never be able to close its quotes and start a second attribute,
close the tag, or open a new element.

These checks feed the rendered markup to a real HTML parser (the standard
library's ``html.parser``) and assert the parse round-trips: one element, the
declared attribute names only, and each value recovered verbatim. An
implementation that assembles raw strings -- or escapes only ``<``/``>``/``&``
but not quotes -- lets a value break out of its attribute, so the parser sees
an extra attribute or a changed structure and the check fails.

Run as a pytest module. Imports the real markupsafe under test.
"""

from __future__ import annotations

from html.parser import HTMLParser

from markupsafe import Markup
from markupsafe.attributes import render_attributes


def _parse_tag(tag: str, attr_markup: str):
    """Parse ``<tag{attr_markup}>`` and return the list of (tag, attrs-dict)."""
    seen: list[tuple[str, dict]] = []

    class _P(HTMLParser):
        def handle_starttag(self, t, attrs):
            seen.append((t, dict(attrs)))

        def handle_startendtag(self, t, attrs):
            seen.append((t, dict(attrs)))

    parser = _P(convert_charrefs=True)
    parser.feed(f"<{tag}{attr_markup}>")
    parser.close()
    return seen


def _assert_roundtrip(attrs: dict, tag: str = "a"):
    """Rendered markup must parse to one `tag` with exactly `attrs` (string values)."""
    markup = str(render_attributes(attrs))
    parsed = _parse_tag(tag, markup)
    assert len(parsed) == 1, (
        f"expected exactly one element, got {len(parsed)}: {parsed!r} "
        f"(markup={markup!r})"
    )
    ptag, pattrs = parsed[0]
    assert ptag == tag, f"tag changed to {ptag!r}: {markup!r}"
    expected = {k: str(v) for k, v in attrs.items()}
    assert pattrs == expected, (
        "attribute set changed when parsed back -- a value broke out of its "
        f"attribute.\n expected={expected!r}\n got     ={pattrs!r}\n "
        f"markup  ={markup!r}"
    )


def test_double_quote_value_stays_one_attribute():
    # A value containing a double quote must not open a second attribute.
    _assert_roundtrip({"title": 'x" onclick="alert(1)'})


def test_tag_breakout_is_neutralized():
    # A value trying to close the tag and inject an element stays inside.
    _assert_roundtrip({"title": 'x"><script>alert(1)</script>'})


def test_close_tag_sequence_stays_inside_value():
    _assert_roundtrip({"value": '">'}, tag="input")


def test_ampersand_is_preserved_as_data():
    # `&` must round-trip as a literal `&`, not start an entity that changes
    # the recovered value.
    _assert_roundtrip({"href": "/search?q=a&b&copy=1"})


def test_angle_brackets_in_value_preserved():
    _assert_roundtrip({"title": "a<b>c"})


def test_injected_attribute_does_not_appear():
    # Explicit: the classic attribute-injection payload must not yield an
    # `onmouseover` attribute in the parsed element.
    markup = str(render_attributes({"title": 'x" onmouseover="steal()'}))
    _, pattrs = _parse_tag("a", markup)[0]
    assert "onmouseover" not in pattrs, (
        f"value broke out and injected an event-handler attribute: {markup!r}"
    )
    assert pattrs.get("title") == 'x" onmouseover="steal()', markup


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
