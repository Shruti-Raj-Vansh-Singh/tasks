# Unpacking an RPM into a staging root

`install_rpm(rpm_path, dest_dir)` unpacks an RPM package into a staging
directory and returns a report of what was written. It builds on the
[`rpmfile`](https://pypi.org/project/rpmfile/) library, which reads the RPM
container format.

## The RPM source

Open an RPM with `rpmfile.open`, which is a context manager:

```python
import rpmfile

with rpmfile.open(rpm_path) as rpm:
    ...
```

An open `RPMFile` exposes:

`headers`
: A dict of the package's header tags (see below).

`getmembers()`
: The archive members, as a list of `RPMInfo` objects in payload order. Each
  `RPMInfo` has `.name`, `.size`, `.mode`, `.isdir`, and `.issymlink`.

`getmember(name)`
: The `RPMInfo` for a single member by name.

`extractfile(member)`
: A read-only binary stream of a member's bytes. `member` may be an `RPMInfo`
  or a member name.

## The header tags

An RPM carries two parallel descriptions of its files. The **payload** is a
compressed CPIO archive of the actual file bytes -- that is what `getmembers()`
and `extractfile()` read. The **header** is a tag dictionary the packager wrote
when the package was built; the file-related tags line up index-for-index:

`basenames`
: list of file base names.

`dirnames` / `dirindexes`
: the directory table and, per file, the index into it. A file's full path is
  `dirnames[dirindexes[i]] + basenames[i]`.

`filesizes`
: list of file sizes in bytes.

`filemodes`
: list of file modes.

`filemd5s`
: list of per-file content digests, one hex string per file. Despite the tag
  name this holds a SHA-256 digest when `filedigestalgo` is `8` (the modern
  default); older packages used MD5.

`filedigestalgo`
: the digest algorithm id for `filemd5s` (`8` = SHA-256, `1` = MD5).

`payloaddigest` / `payloaddigestalgo`
: a digest over the whole compressed payload, if present.

So `filemd5s[i]` is the digest the header records for the file whose base name
is `basenames[i]` and whose size is `filesizes[i]`.

## The report

Return a report of the files written into `dest_dir`. Each entry should carry
the file's `path`, its `digest`, and its `size`, so a caller can see what
landed. The header's `basenames` / `filemd5s` / `filesizes` tables carry
exactly these three fields per file.
