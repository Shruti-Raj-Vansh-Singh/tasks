"""S2 (hidden): the memory bound must cover the codec's own working memory, not
only the size of the output it produces.

An xz stream carries its LZMA dictionary size in its container header. A tiny xz
body (< 100 bytes) that decodes to only a few KB of output can declare a very
large dictionary; a decoder that does not cap the codec's working memory
allocates the whole dictionary the moment it starts decoding -- so an
implementation that bounds *output* size (streaming with a max_length loop)
still blows past the memory limit here, because the payload is small but the
dictionary is huge.

Closing this requires a *different* guard than the output-size loop: bounding the
codec's memory (``lzma.LZMADecompressor(memlimit=...)``, which raises LZMAError)
or refusing the lzma/xz codec for untrusted bodies. Graded by peak traced memory.
"""
import _bomb_harness as H
from kombu.safe_compression import decompress_bounded


def test_xz_dictionary_bomb_stays_under_threshold():
    bomb = H.xz_dict_bomb()  # < 100 bytes on the wire, 256 MB declared dictionary
    assert len(bomb) < 1024  # sanity: this really is a tiny blob

    def run():
        return decompress_bounded(bomb, "xz", H.CAP)

    result, exc, peak = H.measure_peak(run)

    # However the implementation handles it (raise, or return the tiny output),
    # it must not have allocated the declared dictionary.
    assert peak <= H.PEAK_THRESHOLD, (
        "peak %d bytes > threshold %d: the codec allocated its full working "
        "memory (the declared LZMA dictionary) even though the output is tiny; "
        "bounding output size alone does not bound codec memory"
        % (peak, H.PEAK_THRESHOLD))
