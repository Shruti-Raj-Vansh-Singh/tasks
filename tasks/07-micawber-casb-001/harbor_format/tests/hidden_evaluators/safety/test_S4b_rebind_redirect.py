"""S4b (hidden): the address-pinning that S4a requires has to be re-applied at
every redirect hop, not just for the originally supplied URL.

A public URL responds with a redirect to a second host that is a rebinding
name -- public to the lookup that validates the redirect target, private to the
lookup the transport makes to connect to it. An implementation that pins the
resolved address of the *first* URL but then follows the redirect by handing the
target *name* to the transport re-opens the same rebinding gap on the second
hop.

Closing this requires re-resolving, re-validating, and re-pinning the address at
each hop of the redirect chain. This is a distinct requirement from S4a (the
initial URL is validated correctly here; the gap is on the followed hop) and
from S1 (the redirect target is a genuinely public name at validation time, so
a name-based redirect check passes it).
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


@pytest.mark.parametrize(
    "later_addr",
    [
        "10.0.0.5",
        "127.0.0.1",
        "169.254.169.254",
    ],
)
def test_redirect_target_rebind_not_contacted(later_addr):
    H.install()
    try:
        H.reset()
        # A stable public entry host that redirects to the rebinding name.
        H.DNS["entry.example.com"] = "93.184.216.34"
        entry = H.wire(
            302, "Found",
            {"Location": "http://rebind2.example.com/next"}, b"")
        H.ROUTES["entry.example.com"] = entry
        H.ROUTES["93.184.216.34"] = entry
        # The redirect target rebinds: public to the validating lookup, private
        # to the connect-time lookup.
        H.set_rebind("rebind2.example.com", "93.184.216.35", later_addr)
        H.ROUTES["93.184.216.35"] = H.wire(
            200, "OK", {}, b"PUBLIC-HOP-BODY")
        H.ROUTES[later_addr] = H.wire(
            200, "OK", {}, b"SECRET-INTERNAL-DATA")
        try:
            GuardedFetcher().fetch("http://entry.example.com/start")
        except BlockedHostError:
            pass
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()
