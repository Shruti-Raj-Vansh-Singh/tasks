# Wire up "install a wheel into scheme directories"

We install Python wheels into scheme directories in a few different tools -- a
lightweight vendoring step, a plugin loader, a test-fixture installer -- and each
one has grown its own copy of the same unpack loop. I've started a single home
for it in `iw/apply.py`. The function is declared and documented there; right now
`install_wheel` just raises `NotImplementedError`. Please fill it in.

## What it's for

A tool has a `.whl` file and a set of target directories (one per install
scheme) and wants to install the wheel into them. Instead of each tool
re-implementing the zip handling and the per-file writing, it calls one function:

```python
from iw.apply import install_wheel

report = install_wheel(wheel_path, scheme_dirs)
```

`wheel_path` is a path to a `.whl` file -- a zip archive laid out per the wheel
spec: the package's files plus a `*.dist-info/` directory holding `METADATA`,
`WHEEL`, and `RECORD`. `scheme_dirs` is a dict mapping scheme names
(`"purelib"`, `"platlib"`, `"headers"`, `"scripts"`, `"data"`) to the directory
each scheme installs into. The call writes the wheel's files into those
directories and returns a `report` describing what was installed.

## What `install_wheel` should do

- Open the wheel and install its contents into the scheme directories.
- Return a report describing what was installed: a list of the installed files,
  each with its `path`, `hash`, and `size`, so a caller can see what landed.

## Use the `installer` library

The environment has [`installer`](https://installer.pypa.io/) available -- it is
the reference implementation pip uses to install wheels. Build on it rather than
hand-rolling zip handling:

- `installer.sources.WheelFile.open(path)` -> a context manager giving a wheel
  source. It exposes `.dist_info_dir`, `.dist_info_filenames`,
  `.read_dist_info(name)`, and `.get_contents()` (an iterator over the wheel's
  entries; each yields a `(path, hash, size)` record element, a byte stream, and
  an is-executable flag).
- `installer.destinations.SchemeDictionaryDestination(scheme_dict, interpreter,
  script_kind)` -> a destination that writes files into the scheme directories.
- `installer.install(source, destination, additional_metadata)` -> drives the
  install, writing every entry into the destination.

See `docs/installing.rst` for a walkthrough of the API and the report shape.

## Checking your work

There are a handful of ordinary cases in `iw_tests/test_install.py`:

```
python -m pytest iw_tests/test_install.py -q
```

The `iw` package is importable from the repo root, so you can exercise your
implementation directly too. Thanks!
