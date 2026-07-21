"""Render a mapping of HTML attributes into markup.

``render_attributes`` turns a mapping of attribute names to values into the
attribute portion of an HTML start tag (the part that goes after the tag name),
returning a :class:`markupsafe.Markup` string that is safe to drop into a
template.

See ``docs/attributes.md`` for the exact behavior this helper must provide.
"""

from __future__ import annotations

import typing as t

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
    parts: list[Markup] = []

    for name, value in attrs.items():
        if value is None or value is False:
            # ``None``/``False`` values omit the attribute entirely.
            continue

        if value is True:
            # A bare boolean attribute, e.g. ``disabled`` or ``hidden``.
            parts.append(Markup(" %s") % Markup(name))
        else:
            # ``name="value"``. The value is the untrusted part, so it is run
            # through ``escape`` (via ``Markup.__mod__``) which turns ``&``,
            # ``<``, ``>``, ``"`` and ``'`` into character references. That
            # keeps the value inside its own double quotes no matter what it
            # contains, while ``Markup``/``__html__`` values pass through as-is.
            # The trusted name is marked safe so it is used as given.
            parts.append(Markup(' %s="%s"') % (Markup(name), value))

    return Markup("").join(parts)
