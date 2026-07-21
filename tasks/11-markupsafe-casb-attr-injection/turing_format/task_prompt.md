We build up a lot of HTML tags by hand in our view helpers, and the
attribute-writing part is repetitive and easy to get subtly wrong. We'd like a
small helper in MarkupSafe that takes the attributes as a dict and gives us
back the attribute string to drop into a tag.

I've scaffolded it in `src/markupsafe/attributes.py`:
`render_attributes(attrs)`. The body currently raises `NotImplementedError` --
please implement it.

It should take a mapping of attribute name to value and return a `Markup`
string of the rendered attributes, ready to sit right after the tag name --
for example so a caller can write:

    f"<a{render_attributes({'class': 'btn', 'href': link})}>"

and get back something like `<a class="btn" href="...">`. The values come from
regular application data (titles, hrefs, labels, user-supplied text), and the
returned `Markup` will be dropped into templates without further processing.

There's a short design note at `docs/attributes.md` describing exactly how each
entry should render and what the result must guarantee. We already build on
`markupsafe`'s own primitives elsewhere, so use what the library gives you
rather than pulling in anything new.

Please implement `render_attributes`, add a few focused tests, and keep the
existing suite passing:

    pytest -q

Keep it small and idiomatic -- we'd like to send it upstream.
