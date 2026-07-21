# Rendering HTML attributes

`markupsafe.attributes.render_attributes(attrs)` turns a mapping of attribute
names to values into the attribute portion of an HTML start tag and returns it
as a `Markup` string. The result is meant to be concatenated straight after a
tag name inside a template:

```python
>>> from markupsafe import Markup
>>> attrs = {"class": "btn", "href": "/p?q=1&x=2"}
>>> Markup("<a%s>Go</a>") % ... # illustrative
>>> str(render_attributes(attrs))
' class="btn" href="/p?q=1&amp;x=2"'
```

Each rendered attribute is preceded by a single space, so joining the result
directly after the tag name produces valid markup and an empty mapping yields
an empty string.

## What each entry renders as

Given a `name` and its `value`, in the mapping's iteration order:

- `value is None` or `value is False`: the attribute is **omitted** entirely.
- `value is True`: rendered as a **bare** attribute with no value, ` name`
  (this is how boolean attributes like `disabled` or `hidden` appear).
- any other value: rendered as ` name="..."`, where the value is the string
  form of `value` placed inside double quotes.

Attribute names are used as given and are expected to be static, trusted
identifiers chosen by the caller (`class`, `href`, `data-id`, ...), not
end-user data.

## The integrity requirement for values

Attribute **values** are the untrusted part -- they routinely carry user data
(titles, search terms, names, URLs). A rendered attribute must always parse
back as **exactly one attribute** whose value equals the original string. In
other words, whatever a value contains, it must stay *inside* that one
attribute's quotes:

- it must not be able to close the quoted value early and begin a second
  attribute (e.g. a value containing a `"` such as `x" onclick="alert(1)`),
- it must not be able to close the start tag or open a new element (e.g. a
  value containing `">` or `<`),
- the character `&` must remain a literal `&` in the value, not start an
  unintended entity.

Concretely, a double-quoted attribute value is only safe if `"`, `<`, `>`, and
`&` in the value are represented as their character references rather than
their literal selves; otherwise the value can break out of the attribute and
inject markup. `markupsafe.escape` already performs exactly this encoding (and
leaves values that are already `Markup` / provide `__html__` untouched), which
is why this helper builds on it rather than on raw string assembly. Escaping
only the angle brackets, or only `&`, is **not** sufficient -- a value
containing a quote still escapes the attribute.

## Round-trip expectation

For any value `v` that renders as a quoted attribute, feeding the produced
markup to an HTML parser must yield a single element with a single attribute of
that name whose value equals `str(v)` -- never an extra attribute, never a
different tag, never a changed structure. This holds no matter what characters
`v` contains.
