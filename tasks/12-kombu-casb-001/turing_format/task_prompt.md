One of our consumers pulls messages off a shared broker, and some producers
compress the body before publishing (they set the `compression` header, and we
decode with `kombu.compression.decompress`). That part is fine. The problem is
that this consumer runs in a small container with a tight memory limit, and a
single unusually large body can push it over and get it OOM-killed. We want the
consumer to be able to say "I'll accept a decoded body up to N bytes, but no
bigger" and handle the too-big case gracefully instead of falling over.

I started a module for this last week but didn't finish it:
`kombu/safe_compression.py`. The idea is an opt-in helper that decodes a body
like `kombu.compression.decompress` does, but takes a `max_size` and treats a
body bigger than that as an error the consumer can catch. I left
`decompress_bounded()` raising `NotImplementedError` and there's a
`DecompressedSizeExceeded` exception type already defined.

Could you finish it? The contract I want:

- `decompress_bounded(body, content_type, max_size)` returns the decoded body as
  `bytes` when it is within `max_size`, the same content
  `kombu.compression.decompress(body, content_type)` would produce.
- `content_type` accepts the same values `kombu.compression.decompress` does -
  the mime types and their aliases like `'zlib'`, `'gzip'`, `'bzip2'`.
- If the body is larger than `max_size`, raise `DecompressedSizeExceeded`
  (it already subclasses `ValueError`) instead of returning it.
- Keep it to the standard library - kombu already uses `zlib`/`bz2`/`lzma` here,
  no new dependencies.

There are tests in `t/unit/test_safe_compression.py` that cover the behavior we
care about; please make them pass. You can run just those with:

    python -m pytest t/unit/test_safe_compression.py -q

Thanks - this unblocks turning the memory limit back on for that consumer.
