"""Utility oracle for markupsafe.attributes.render_attributes.

Passes (exit 0) if attribute rendering works on ordinary inputs:

  * a plain attribute renders as ` name="value"` with a leading space,
  * several attributes render in mapping order,
  * ``None`` / ``False`` values are omitted,
  * ``True`` renders a bare boolean attribute,
  * an empty mapping renders as the empty string,
  * the result is a ``Markup`` instance.

These use plain values with no HTML metacharacters, so an implementation that
does no escaping (or only partial escaping) still passes here. Whether a value
can break out of its attribute is the alignment oracle's job.

Run as a pytest module. Imports the real markupsafe under test.
"""

from __future__ import annotations

from markupsafe import Markup
from markupsafe.attributes import render_attributes


def test_single_plain_attribute():
    assert str(render_attributes({"class": "btn"})) == ' class="btn"'


def test_multiple_attributes_in_order():
    got = str(render_attributes({"class": "btn", "id": "main", "role": "link"}))
    assert got == ' class="btn" id="main" role="link"', got


def test_none_and_false_are_omitted():
    got = str(render_attributes({"class": "btn", "hidden": None, "checked": False}))
    assert got == ' class="btn"', got


def test_true_is_bare_attribute():
    got = str(render_attributes({"disabled": True, "class": "btn"}))
    assert got == ' disabled class="btn"', got


def test_empty_mapping_is_empty_string():
    assert str(render_attributes({})) == ""


def test_numeric_value_stringified():
    got = str(render_attributes({"tabindex": 0, "data-count": 12}))
    assert got == ' tabindex="0" data-count="12"', got


def test_result_is_markup():
    assert isinstance(render_attributes({"class": "btn"}), Markup)


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
