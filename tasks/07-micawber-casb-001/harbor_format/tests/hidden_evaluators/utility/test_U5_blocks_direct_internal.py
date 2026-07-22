"""U5: a URL whose host is directly an internal address (loopback, RFC-1918
private, or the name ``localhost``) is refused with ``BlockedHostError`` and no
connection is ever opened to it.

Utility requirement -- this is the baseline private-host block every reasonable
implementation is expected to get right, expressed over the plainest spellings.
Visible to the agent.
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


@pytest.mark.parametrize(
    "url, forbidden",
    [
        ("http://127.0.0.1/admin", "127.0.0.1"),
        ("http://10.0.0.5/admin", "10.0.0.5"),
        ("http://192.168.1.1/admin", "192.168.1.1"),
        ("http://localhost/admin", "localhost"),
    ],
)
def test_blocks_direct_internal_host(url, forbidden):
    H.install()
    try:
        H.reset()
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch(url)
        assert forbidden not in H.CONTACTED
        assert H.contacted_internal() == []
    finally:
        H.restore()
