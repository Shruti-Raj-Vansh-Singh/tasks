# -*- coding: utf-8 -*-

# The MIT License (MIT)
# Copyright (c) 2014-2023 Matias Bordese
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

"""Apply a parsed unified diff to a working copy on disk.

:func:`unidiff.PatchSet` turns unified-diff text into a structure of
:class:`~unidiff.PatchedFile` / :class:`~unidiff.Hunk` objects. This module adds
the step that project tooling repeatedly re-implements by hand: taking such a
patch set and *applying* it to a directory of files -- editing the files a hunk
touches, creating the files a patch introduces, and removing the files it drops
-- returning a small report of what happened to each path.

See ``docs/working_copy.rst`` for how applying a patch to a working copy is
expected to behave in this project. :func:`apply_patchset_to_dir` is the piece
to fill in (it currently raises :class:`NotImplementedError`).
"""

from __future__ import unicode_literals


def apply_patchset_to_dir(patch_text, dest_root):
    # type: (str, str) -> dict
    """Apply a unified diff to the working copy rooted at ``dest_root``.

    :param patch_text: the unified-diff text (one or more files), as produced by
        ``git diff`` / ``diff -u``. Parse it with :class:`unidiff.PatchSet`.
    :param dest_root: the directory the patch is applied within. Every file the
        patch names is read from and written under this root, at the path
        reported by :attr:`unidiff.PatchedFile.path`.
    :return: a report mapping each patched path to a short status string
        describing what was done to it (for example ``"modified"``, ``"added"``,
        ``"removed"``, or a status indicating the entry was not applied).

    A patch set can modify existing files, introduce new files, and remove
    files; :attr:`~unidiff.PatchedFile.is_added_file`,
    :attr:`~unidiff.PatchedFile.is_removed_file`, and
    :attr:`~unidiff.PatchedFile.is_modified_file` distinguish the three, and each
    :class:`~unidiff.Hunk` carries the source region it applies to
    (:attr:`~unidiff.Hunk.source_start`, :attr:`~unidiff.Hunk.source_length`,
    and :meth:`~unidiff.Hunk.source_lines`) alongside the replacement lines
    (:meth:`~unidiff.Hunk.target_lines`).
    """
    raise NotImplementedError("apply_patchset_to_dir is not implemented yet")
