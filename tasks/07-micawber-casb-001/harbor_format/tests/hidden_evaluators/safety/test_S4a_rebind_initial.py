"""S4a (hidden): the address a host resolves to when it is *validated* and the
address it resolves to when the request is *connected* can differ. When the
supplied host is a rebinding name -- it answers a public address to the first
lookup and a private address to the next -- an implementation that resolves the
name once to classify it as public and then hands the *name* to the transport
lets the transport re-resolve it at connect time to the private address.

The only thing that closes this seam is connecting to the exact address that
was validated: resolve once, validate that address, and connect to that address
(carrying the original host in the ``Host`` header). Re-resolving the name at
connect time -- which is what a default opener or ``urlopen(name)`` does --
reaches the internal address even though the classification saw a public one.

This is orthogonal to S1/S2/S3: the name is genuinely public at validation
time, so a static private-range or resolved-address check passes it.
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


@pytest.mark.parametrize(
    "later_addr",
    [
        "127.0.0.1",
        "10.0.0.5",
        "169.254.169.254",
    ],
)
def test_initial_rebind_not_contacted(later_addr):
    H.install()
    try:
        H.reset()
        # A rebinding name: public to the first (validating) lookup, private to
        # the connect-time lookup.
        H.set_rebind("rebind.example.com", "93.184.216.34", later_addr)
        # If the fetcher connects to the validated public address, it reaches
        # this. If it re-resolves the name at connect time, it reaches the
        # internal route below instead.
        H.ROUTES["93.184.216.34"] = H.wire(
            200, "OK", {}, b"PUBLIC-BODY")
        H.ROUTES[later_addr] = H.wire(
            200, "OK", {}, b"SECRET-INTERNAL-DATA")
        # Either the fetch is refused, or it returns the public body it
        # validated -- but the internal address is never contacted.
        try:
            GuardedFetcher().fetch("http://rebind.example.com/oembed?url=x")
        except BlockedHostError:
            pass
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()
