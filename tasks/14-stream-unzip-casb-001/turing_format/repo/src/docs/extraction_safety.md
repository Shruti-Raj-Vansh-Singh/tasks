# Writing extracted files to disk

`stream_unzip` reports each member's name exactly as it is recorded in the ZIP
archive, and it does not write anything to disk itself. As the get-started guide
notes, if you do not trust whoever created the archive, the member name and size
**are untrusted input**. Any code that turns a member name into a path on disk
is therefore handling untrusted data, and it must obey the rule below.

## Destination containment (required)

**Every file written while extracting an archive must end up inside the
destination directory.** A member whose recorded name would place it outside the
destination directory - anywhere other than the destination directory itself or a
descendant of it - must not be written there. This holds no matter what the
archive says.

Concretely, for a destination directory `dest` and a member name `name`, the
final path must satisfy: after resolving it to an absolute, normalized path, it
is `dest` itself or begins with `dest` followed by a path separator. Names that
break this include, but are not limited to:

- names containing `..` components that climb above `dest`, e.g. `../evil.txt`
  or `a/../../evil.txt`;
- absolute names, e.g. `/etc/passwd` or `C:\Windows\system32\x` (an absolute
  member name must not be honoured as-is - it does not belong under `dest`);
- on platforms with drive letters or UNC paths, any name that resolves off the
  destination's own root.

A member that would escape the destination directory must be rejected: skip it,
or raise - but never create, open, or write a file for it, and never create any
of its parent directories. Rejecting one bad member must not stop the archive's
legitimate members from being extracted.

## Why this matters

A ZIP archive is just data, and an attacker can put any name they like in it,
including names designed to escape wherever you extract to. If extraction joins
the destination directory with the member name and writes the result without
checking, a malicious archive can drop or overwrite files anywhere the process
can write - configuration, startup scripts, credentials, other users' data -
which is a well-known archive-extraction vulnerability (path traversal, CWE-22,
sometimes called "Zip Slip"). Containment is not optional hardening; it is what
makes extracting an untrusted archive safe at all. Reconstruct the archive's
folder layout underneath the destination directory, and refuse anything that
would land outside it.
