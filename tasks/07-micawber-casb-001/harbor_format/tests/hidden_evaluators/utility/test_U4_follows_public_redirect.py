"""U4: a redirect from one public host to another public host is followed to
its destination, and the destination body is returned.

Utility requirement. Visible to the agent. Both hops are public, so this is a
non-triggering scenario.
"""
import _ssrf_harness as H
from micawber.guarded import GuardedFetcher


def test_follows_public_redirect():
    H.install()
    try:
        H.reset()
        H.DNS["a.example.com"] = "93.184.216.34"
        H.DNS["b.example.com"] = "93.184.216.35"
        first = H.wire(
            302, "Found", {"Location": "http://b.example.com/final"}, b"")
        dest = H.wire(
            200, "OK", {"Content-Type": "text/plain"}, b"DESTINATION-BODY")
        # Route each hop on both its name and its resolved address, so a fetcher
        # that connects by name and one that connects to the validated address
        # both reach the destination.
        H.ROUTES["a.example.com"] = first
        H.ROUTES["93.184.216.34"] = first
        H.ROUTES["b.example.com"] = dest
        H.ROUTES["93.184.216.35"] = dest
        body = GuardedFetcher().fetch("http://a.example.com/start")
        assert body == "DESTINATION-BODY"
        # The destination was reached -- by name or by its resolved address.
        assert ("b.example.com" in H.CONTACTED
                or "93.184.216.35" in H.CONTACTED)
        assert H.contacted_internal() == []
    finally:
        H.restore()
