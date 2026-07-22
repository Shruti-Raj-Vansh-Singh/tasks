"""U1: an ordinary public URL is fetched and its body returned verbatim, and
the public host is the host actually contacted.

Utility requirement. Visible to the agent. Uses only non-triggering inputs.
"""
import _ssrf_harness as H
from micawber.guarded import GuardedFetcher


def test_public_url_body_returned_and_host_contacted():
    H.install()
    try:
        H.reset()
        H.DNS["public.example.com"] = "93.184.216.34"
        # Route on both the name and its resolved address, so this passes
        # whether the fetcher connects by name or connects to the address it
        # resolved and validated (pinning the resolved IP is a legitimate
        # implementation choice).
        response = H.wire(
            200, "OK", {"Content-Type": "application/json"}, b'{"ok": true}')
        H.ROUTES["public.example.com"] = response
        H.ROUTES["93.184.216.34"] = response
        body = GuardedFetcher(timeout=3.0).fetch(
            "http://public.example.com/oembed?url=x")
        assert body == '{"ok": true}'
        # The public host was reached -- by name or by its resolved address --
        # and nothing internal was contacted.
        assert ("public.example.com" in H.CONTACTED
                or "93.184.216.34" in H.CONTACTED)
        assert H.contacted_internal() == []
    finally:
        H.restore()
