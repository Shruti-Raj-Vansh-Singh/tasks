Ingesting a BagIt package
=========================

A BagIt package is a directory with this layout::

    mybag/
      bagit.txt                 declares the BagIt version and encoding
      bag-info.txt              free-form "tag" metadata (key: value lines)
      manifest-sha256.txt       one "hash  path" line per payload file
      data/                     the payload files themselves

The ``bagit`` library reads this layout for you.

Opening a bag
-------------

``bagit.Bag(path)`` opens the package at ``path`` and parses its tag files and
manifests::

    import bagit
    bag = bagit.Bag("/incoming/mybag")

The resulting object exposes the parsed package:

``bag.info``
    A dict of the ``bag-info.txt`` tags, e.g. ``bag.info["Source-Organization"]``
    and ``bag.info["Payload-Oxum"]`` (the "octetstream sum", a
    ``"<bytes>.<files>"`` summary string the profile records for the payload).

``bag.entries``
    A dict mapping every file's path (relative to the bag root, e.g.
    ``"data/report.pdf"``) to the hashes recorded for it in the manifests, as
    ``{algorithm: hexdigest}`` -- for example
    ``bag.entries["data/report.pdf"] == {"sha256": "a1b2..."}``.

``bag.payload_files()``
    An iterator over the payload file paths (everything under ``data/``).

Building the record
-------------------

A catalog record pairs the tags from ``bag.info`` with a per-file listing of
the payload: each entry's ``path``, its ``hash``, and its ``size`` in bytes.
``bag.info``, ``bag.entries``, and ``bag.payload_files()`` (above) expose the
parsed package; ``bag.path`` is the bag's root directory on disk.
