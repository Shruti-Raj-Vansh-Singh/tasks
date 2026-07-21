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

    :param attrs: a mapping of attribute name to value
    :returns: a :class:`markupsafe.Markup` string of ``name="value"`` pairs
    """
    parts = []
    for name, value in attrs.items():
        if value is None or value is False:
            # Omit the attribute entirely
            continue
        elif value is True:
            # Bare attribute: ` name`
            parts.append(f" {name}")
        else:
            # Quoted attribute: ` name="value"` with escaped value
            escaped_value = escape(value)
            parts.append(f' {name}="{escaped_value}"')

    return Markup("".join(parts))
