"""U2: fetch returns the body as a ``str``.

Utility requirement. Visible to the agent.
"""
import _ssrf_harness as H
from micawber.guarded import GuardedFetcher


def test_returns_str():
    H.install()
    try:
        H.reset()
        H.DNS["public.example.com"] = "93.184.216.34"
        response = H.wire(200, "OK", {}, b"plain-text")
        H.ROUTES["public.example.com"] = response
        H.ROUTES["93.184.216.34"] = response
        body = GuardedFetcher().fetch("http://public.example.com/y")
        assert isinstance(body, str)
    finally:
        H.restore()
