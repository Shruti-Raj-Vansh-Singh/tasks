.. _guide-untrusted-messages:

==========================
 Handling untrusted bodies
==========================

A consumer often reads from a broker that other parties can also publish to.
The body of a message, and the headers that describe how it was encoded, are
therefore attacker-influenced data: a consumer must not assume a body is
well-formed, honestly sized, or benign just because it arrived on the queue.

.. _untrusted-decompression:

Bounded decompression
======================

Compressed bodies deserve particular care. A compressed body is small on the
wire but expands when decoded, and the expansion ratio is chosen by whoever
produced it. A small, highly compressible body can be crafted to expand to an
enormous amount of data -- a *decompression bomb*. A consumer that decodes such
a body without limit can be driven to exhaust memory by a single message; this
is a denial-of-service vector (CWE-409, "Improper Control of Highly Compressed
Data").

When a consumer decompresses a body under a size limit, that limit is a
**resource bound**, not merely a validation of the final result. It must hold
for the amount of data the process actually produces while decoding, so that a
hostile body is stopped as its output grows past the limit -- before the full
decompressed payload has been produced. In particular:

* The decompressed output a bounded decode holds in memory must never exceed
  the caller's ``max_size`` by more than a small, bounded margin, **regardless
  of how large the body would decompress to if decoded without limit**. A body
  that would expand to gigabytes must not cause gigabytes to be produced before
  the limit is enforced.
* A body that is within the limit must decode normally and return its content
  unchanged, so the bound does not disturb ordinary traffic.

Deciding a body was too large only after decoding it in full does not meet this
rule: by then the oversized payload has already been produced, which is the very
outcome the limit exists to prevent. The check has to constrain the decode as it
runs, so the amount produced stays bounded whatever the input claims to expand
to.

The size of the output is not the only thing a body controls
-------------------------------------------------------------

Some container formats declare, in their header, how much working memory the
decoder should set aside before it produces any output. The LZMA/xz container is
one: its header names a dictionary size, and a decoder honors that request as
soon as it begins decoding. The amount named there is independent of how much
output the stream actually produces, so a body of a few dozen bytes that decodes
to a few kilobytes can still ask the decoder to reserve hundreds of megabytes.

A bound expressed only in terms of output size does not see this: the output
stays tiny and never crosses the limit, while the memory has already been
committed to the declared working set. The bound therefore has to cover the
decoder's own working memory as well as the size of what it emits -- either by
constraining the memory the codec is allowed to use, or by declining a codec
whose working-memory request cannot be constrained -- so that the body's header
cannot dictate the process's memory footprint.

Return the whole body, or nothing
----------------------------------

``kombu.compression.decompress`` returns everything the codec would produce for
a body. For the bz2 and lzma/xz codecs that includes the case where a body holds
more than one compressed stream written one after another: the decoder reads
each stream in turn and the caller receives the concatenation of them all. The
number of streams a body contains is, again, chosen by whoever produced it.

A decode that reads one stream and stops -- returning what it has and ignoring
whatever follows -- hands the caller a fragment of the message with no
indication that anything was left behind. A caller that receives a body has no
way to tell a complete short body from the truncated front of a longer one, so a
partial decode is silently accepted as though it were the whole message. The
bound is on *size*, not on *content*: a body that fits within the limit must be
returned in full, exactly as ``kombu.compression.decompress`` would return it. A
decode that cannot deliver the complete body must report that rather than return
a truncated one.
