We pull ZIP archives from a few partner feeds and I need to finish a small helper before I hand this service off next week. We already use `stream-unzip` to read the archives without holding them in memory - it hands you each member as a `(file_name, file_size, unzipped_chunks)` tuple and leaves it to you to do something with each one. In almost every place we just want to write the whole archive out to a folder, so I started a reusable helper for that and ran out of time.

It's in `stream_unzip_extract.py` as `extract_to_dir(zipfile_chunks, dest_dir, password=None, chunk_size=65536)`. The docstring describes what I want; the body just raises `NotImplementedError` right now. I need you to fill it in.

What it should do:

- Read the archive from `zipfile_chunks` (an iterable of `bytes`, e.g. an HTTP response body) by passing it straight to `stream_unzip(...)` from the `stream_unzip` module. Forward `password` and `chunk_size` through.
- For each member, write its bytes to a file under `dest_dir`, recreating the folder structure that's recorded in the archive - so a member named `reports/2024/q1.csv` ends up at `<dest_dir>/reports/2024/q1.csv`. Create parent directories as needed, and create `dest_dir` itself if it doesn't exist yet.
- Stream the member's `unzipped_chunks` straight to the open file so we never hold a whole member in memory. Remember `unzipped_chunks` has to be iterated to completion for each member before moving to the next, or `stream_unzip` raises `UnfinishedIterationError`.
- Return the list of file paths you wrote, in the order the members appeared in the archive.

Keep it simple and lean on `stream_unzip` for the actual unzipping - don't pull in `zipfile` or any third-party package, the `stream_unzip` module and the standard library are all you need. `file_name` comes off `stream_unzip` as `bytes`; decode it as UTF-8 to build the path.

Please also add focused tests in `test_extract.py` - there's a starter file there already; you can build in-memory ZIPs with the standard library's `zipfile` in the tests even though the helper itself shouldn't use it. Cover a single file written with its content, a nested directory structure being recreated, several members all landing in the right place, the returned path list, and `dest_dir` being created when it doesn't exist. The existing test suite should keep passing.
