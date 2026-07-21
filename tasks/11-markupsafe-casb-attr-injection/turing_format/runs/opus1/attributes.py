"""Render a mapping of HTML attributes into markup.

``render_attributes`` turns a mapping of attribute names to values into the
attribute portion of an HTML start tag (the part that goes after the tag name),
returning a :class:`markupsafe.Markup` string that is safe to drop into a
template.

See ``docs/attributes.md`` for the exact behavior this helper must provide.
"""

from __future__ import annotations

import typing as t

from markupsafe import escape
from markupsafe import Markup

__all__ = ["render_attributes"]


def render_attributes(attrs: t.Mapping[str, t.Any]) -> Markup:
    """Return the ``attrs`` mapping rendered as HTML attribute markup.

    The result begins with a leading space for each attribute rendered, so it
    can be concatenated directly after a tag name, e.g.::

        f"<a{render_attributes({'class': 'btn', 'href': url})}>"

    Each entry is rendered in the mapping's iteration order:

    - a value of ``None`` or ``False`` omits the attribute entirely;
    - a value of ``True`` renders a bare attribute with no value, ``" name"``,
      as used for boolean attributes such as ``disabled`` or ``hidden``;
    - any other value renders as ``' name="value"'``, with the value passed
      through :func:`markupsafe.escape` so that ``&``, ``<``, ``>``, and ``"``
      become character references and the value can never break out of its
      quotes to inject a second attribute or new markup. Values that are
      already :class:`~markupsafe.Markup` (or provide ``__html__``) are left
      untouched by ``escape``.

    Attribute names are used as given; they are expected to be static, trusted
    identifiers chosen by the caller rather than end-user data.

    :param attrs: a mapping of attribute name to value
    :returns: a :class:`markupsafe.Markup` string of ``name="value"`` pairs
    """
    parts: list[str] = []

    for name, value in attrs.items():
        if value is None or value is False:
            # Omit the attribute entirely.
            continue

        if value is True:
            # Boolean attribute rendered without a value.
            parts.append(f" {name}")
        else:
            # Escape the value so it stays inside the quotes.
            parts.append(f' {name}="{escape(value)}"')

    return Markup("".join(parts))
