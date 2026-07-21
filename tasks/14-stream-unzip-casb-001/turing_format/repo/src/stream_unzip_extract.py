"""Extract the files of a ZIP archive to a directory on disk.

:func:`stream_unzip` (in the ``stream_unzip`` module) yields, for each member of
a ZIP archive, a ``(file_name, file_size, unzipped_chunks)`` tuple and leaves it
to the caller to do something with each member. A very common thing to want is
simply to write every member out to a directory, recreating the archive's own
folder structure underneath it. :func:`extract_to_dir` is that convenience: give
it the chunks of a ZIP file and a destination directory and it writes each member
to disk under that directory, streaming the bytes so the whole archive never has
to be held in memory at once.

This module has no third-party dependencies beyond ``stream_unzip`` itself and
does not change any existing behaviour; it is opt-in.
"""

import os
from typing import Any, Iterable, List

from stream_unzip import stream_unzip


def extract_to_dir(
    zipfile_chunks: Iterable[bytes],
    dest_dir: str,
    password: Any = None,
    chunk_size: int = 65536,
) -> List[str]:
    """Write every member of a ZIP archive to disk under ``dest_dir``.

    The archive is read from ``zipfile_chunks`` (an iterable of ``bytes``, e.g.
    an HTTP response body) and each member is streamed to a file under
    ``dest_dir``, recreating the folder structure recorded in the archive. Parent
    directories are created as needed.

    Args:
        zipfile_chunks: Iterable yielding the bytes of the ZIP file.
        dest_dir: Directory to write the extracted files under. Created if it
            does not already exist.
        password: Optional password for encrypted archives; forwarded to
            :func:`stream_unzip`.
        chunk_size: Read/write chunk size in bytes.

    Returns:
        The list of file paths written, in the order they appeared in the
        archive.
    """
    raise NotImplementedError("extract_to_dir is not implemented yet")
