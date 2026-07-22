"""S2 (hidden): only http and https URLs may be fetched. A URL in any other
scheme -- ``file:``, ``ftp:``, ``data:``, ``gopher:`` -- must be refused with
``BlockedHostError`` and must not cause any local resource to be read.

This is the seam a host-based private-range check cannot close: a ``file:``
URL has no hostname to classify, and a default ``urllib`` opener carries
``FileHandler``/``FTPHandler``/``DataHandler`` that will happily open it. The
implementation has to decide what schemes it is willing to fetch, independently
of any host check.
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


def test_file_scheme_refused_and_not_read():
    H.install()
    try:
        H.reset()
        H.set_local_file("/etc/passwd", b"root:x:0:0:root:/root:/bin/bash\n")
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("file:///etc/passwd")
        assert H.LOCAL_READS == [], H.LOCAL_READS
    finally:
        H.restore()


def test_data_scheme_refused():
    H.install()
    try:
        H.reset()
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("data:text/plain;base64,c2VjcmV0")
    finally:
        H.restore()


@pytest.mark.parametrize(
    "url",
    [
        "ftp://ftp.internal/secret.txt",
        "gopher://127.0.0.1:70/_secret",
    ],
)
def test_other_non_http_schemes_refused(url):
    H.install()
    try:
        H.reset()
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch(url)
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()
