Applying a patch to a working copy
==================================

This page describes the ``apply_patchset_to_dir`` helper: it takes a unified
diff and edits a tree of files under a root directory to match it. It is used
by any tool that ships a change as a diff -- a review tool that lands a proposed
change, a migration that ships as a diff, a bot that applies a contributor's
patch.

The patch text
--------------

``patch_text`` is a unified diff as produced by ``git diff`` or ``diff -u``. It
may name several files at once. Parse it with :class:`unidiff.PatchSet`, which
yields one :class:`~unidiff.PatchedFile` per file, each carrying its
:class:`~unidiff.Hunk` objects.

Each patched file is one of three kinds, distinguished by
:attr:`~unidiff.PatchedFile.is_added_file`,
:attr:`~unidiff.PatchedFile.is_removed_file`, and
:attr:`~unidiff.PatchedFile.is_modified_file`. Its
:attr:`~unidiff.PatchedFile.path` is the file it names under the root.

The hunks
---------

Each :class:`~unidiff.Hunk` names a source region -- its
:attr:`~unidiff.Hunk.source_start` (1-based) and
:attr:`~unidiff.Hunk.source_length` -- and exposes two line views:
:meth:`~unidiff.Hunk.source_lines` (the context and removed lines) and
:meth:`~unidiff.Hunk.target_lines` (the context and added lines). Each
:class:`~unidiff.Line` carries its text in ``.value`` (including the trailing
newline).

The report
----------

``apply_patchset_to_dir`` returns a mapping of each patched path to a short
status string, so a caller can see what happened to each file it named.
