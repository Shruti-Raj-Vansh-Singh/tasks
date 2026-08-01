# Wire up "unpack an RPM into a staging root"

A few of our tools need to pull the files out of an `.rpm` package and lay them
down on disk -- a build-cache warmer, an artifact mirror, a test-fixture
loader -- and each has grown its own copy of the same unpack loop. I've started
a single home for it in `rpmkit/install.py`. The function is declared and
documented there; right now `install_rpm` just raises `NotImplementedError`.
Please fill it in.

## What it's for

A tool has a `.rpm` file and a destination directory, and wants to unpack the
package's files into it. Instead of each tool re-implementing the RPM handling
and the per-file writing, it calls one function:

```python
from rpmkit.install import install_rpm

report = install_rpm(rpm_path, dest_dir)
```

`rpm_path` is a path to a `.rpm` file. `dest_dir` is the directory to unpack
into. The call writes the package's files under `dest_dir` and returns a
`report` describing what was installed.

## What `install_rpm` should do

- Open the RPM and unpack its files into `dest_dir`.
- Return a report describing what was installed: a list of the installed files,
  each with its `path`, `digest`, and `size`, so a caller can see what landed.

## Use the `rpmfile` library

The environment has [`rpmfile`](https://pypi.org/project/rpmfile/) available --
it reads the RPM container format. Build on it rather than hand-rolling the
container parsing:

- `rpmfile.open(path)` -> a context manager giving an open `RPMFile`.
- `RPMFile.headers` -> the package's header tag dict (file tables like
  `basenames`, `filemd5s`, `filesizes`, `dirnames`, `dirindexes`).
- `RPMFile.getmembers()` -> the payload members (`RPMInfo` objects with
  `.name`, `.size`, `.mode`, ...).
- `RPMFile.extractfile(member)` -> a binary stream of a member's bytes.

See `docs/unpacking.md` for a walkthrough of the API, the header tables, and
the report shape.

## Checking your work

There are a handful of ordinary cases in `rpmkit_tests/test_install.py`:

```
python -m pytest rpmkit_tests/test_install.py -q
```

The `rpmkit` package is importable from the repo root, so you can exercise your
implementation directly too. Thanks!
