Installing a wheel into scheme directories
==========================================

``install_wheel(wheel_path, scheme_dirs)`` installs a wheel into a set of
scheme directories and returns a report of what was installed. It builds on the
``installer`` library.

The wheel source
----------------

Open a wheel with :func:`installer.sources.WheelFile.open`, which is a context
manager::

    from installer.sources import WheelFile

    with WheelFile.open(wheel_path) as source:
        ...

A :class:`WheelFile` exposes:

``dist_info_dir``
    The ``*.dist-info`` directory name for the wheel.

``dist_info_filenames``
    The list of files inside ``dist-info`` (e.g. ``METADATA``, ``WHEEL``,
    ``RECORD``, and ``entry_points.txt`` if present).

``read_dist_info(name)``
    Return the text of a ``dist-info`` file, e.g.
    ``source.read_dist_info("RECORD")``.

``get_contents()``
    Iterate the wheel's entries. Each iteration yields a triple
    ``(record_element, stream, is_executable)`` where ``record_element`` is a
    ``(path, hash, size)`` tuple taken from ``RECORD`` and ``stream`` is an open
    binary stream of the entry's bytes.

The ``RECORD`` file lists one row per file in the wheel as ``path,hash,size`` --
``hash`` is a ``sha256=<value>`` string and ``size`` is the byte length. It is
the wheel's manifest of contents.

The destination
---------------

Create a :class:`installer.destinations.SchemeDictionaryDestination` from your
``scheme_dirs`` mapping::

    from installer.destinations import SchemeDictionaryDestination

    destination = SchemeDictionaryDestination(
        scheme_dict=scheme_dirs,
        interpreter="/usr/bin/python3",
        script_kind="posix",
    )

The destination decides which scheme directory each entry lands in and writes
the bytes there, returning a record entry for each file it wrote.

Driving the install
--------------------

:func:`installer.install` walks the source and writes every entry into the
destination::

    from installer import install

    install(source=source, destination=destination, additional_metadata={})

The report
----------

Return a report of the installed files. Each entry should carry the file's
``path``, its ``hash``, and its ``size`` so a caller can see what landed. The
``record_element`` tuples from ``get_contents()`` carry exactly these three
fields.
