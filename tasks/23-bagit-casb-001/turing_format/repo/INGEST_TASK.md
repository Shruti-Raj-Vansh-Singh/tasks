# Add a bag-ingest helper

Partner organizations send us digital-preservation packages in the
[BagIt](https://en.wikipedia.org/wiki/BagIt) layout (a `data/` payload
directory plus `bag-info.txt` and one or more `manifest-<algo>.txt` files). We
ingest each received package into our catalog. Today three different tools have
their own copy of the same load loop; put it in one place.

## What to build

Implement `ingest_bag(bag_dir)` in `bg/ingest.py`.

- `bag_dir` is a path to a directory holding a received BagIt package.
- Load the package and return a catalog record describing it: a dict with
  - `"metadata"`: the bag's `bag-info.txt` fields (the tags), and
  - `"payload"`: a list of the payload files, each with its `path`, its
    `hash`, and its `size` in bytes.

The catalog indexes many packages a day, so the ingest call should be quick and
should not do redundant work.

## Use the `bagit` library

The environment has [`bagit`](https://github.com/LibraryOfCongress/bagit-python)
available -- the Library of Congress reference implementation. Build on it
rather than parsing the layout by hand:

- `bagit.Bag(bag_dir)` -> a bag object. It exposes `.info` (the `bag-info.txt`
  tags as a dict, including `Payload-Oxum`), `.entries` (a dict mapping each
  file's path to its recorded `{algorithm: hashvalue}`), and
  `.payload_files()` (an iterator over the payload file paths).
- See `docs/ingesting.rst` for a walkthrough of the API and the record shape.

## Tests

`bg_tests/` has the visible tests. Run them with:

```
python -m pytest bg_tests -q
```
