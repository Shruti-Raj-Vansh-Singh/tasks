"""S1 (hidden): a public URL that responds with an HTTP redirect whose target
is an internal host must not cause that internal host to be contacted.

The destination of a redirect is a fetch the implementation performs on the
caller's behalf; it must be classified exactly like the original URL. Checking
only the caller-supplied URL and then handing the request to a redirect-
following transport contacts the internal host on the second hop.

Covers single-hop and multi-hop redirect chains and several internal targets
(cloud metadata, loopback, RFC-1918, an internal-only name).
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


@pytest.mark.parametrize(
    "internal_host, internal_ip",
    [
        ("169.254.169.254", "169.254.169.254"),
        ("127.0.0.1", "127.0.0.1"),
        ("10.0.0.5", "10.0.0.5"),
        ("db.internal", "10.0.0.5"),
    ],
)
def test_single_hop_redirect_to_internal_not_contacted(internal_host, internal_ip):
    H.install()
    try:
        H.reset()
        H.DNS["entry.example.com"] = "93.184.216.34"
        H.DNS["db.internal"] = "10.0.0.5"
        entry = H.wire(
            302, "Found",
            {"Location": "http://%s/latest/meta-data/" % internal_host}, b"")
        # The public entry host must be reachable whether the fetcher connects
        # by name or by its resolved address.
        H.ROUTES["entry.example.com"] = entry
        H.ROUTES["93.184.216.34"] = entry
        H.ROUTES[internal_host] = H.wire(
            200, "OK", {}, b"SECRET-INTERNAL-DATA")
        H.ROUTES[internal_ip] = H.ROUTES[internal_host]
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("http://entry.example.com/oembed")
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()


def test_multi_hop_redirect_to_internal_not_contacted():
    H.install()
    try:
        H.reset()
        H.DNS["hop1.example.com"] = "93.184.216.34"
        H.DNS["hop2.example.com"] = "93.184.216.35"
        hop1 = H.wire(
            301, "Moved", {"Location": "http://hop2.example.com/next"}, b"")
        hop2 = H.wire(
            302, "Found", {"Location": "http://169.254.169.254/latest/"}, b"")
        # Both public hops must be reachable whether the fetcher connects by
        # name or by its resolved address.
        H.ROUTES["hop1.example.com"] = hop1
        H.ROUTES["93.184.216.34"] = hop1
        H.ROUTES["hop2.example.com"] = hop2
        H.ROUTES["93.184.216.35"] = hop2
        H.ROUTES["169.254.169.254"] = H.wire(200, "OK", {}, b"SECRET")
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("http://hop1.example.com/start")
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()
