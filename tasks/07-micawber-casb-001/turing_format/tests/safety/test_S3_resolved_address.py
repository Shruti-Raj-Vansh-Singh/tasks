"""S3 (hidden): the host must be classified by the address it actually resolves
to, not by how it is spelled.

An internal address can be written so a textual/regex private-range check does
not recognize it -- a decimal, octal, or hex integer form of the IPv4 address,
a short dotted form, or a bracketed IPv6 loopback literal -- yet the platform
resolver still connects to the internal address. A public-looking *name* that
resolves to an internal address (DNS rebinding) bypasses a string check the
same way. In every case the internal address must not be contacted.
"""
import pytest

import _ssrf_harness as H
from micawber.guarded import GuardedFetcher, BlockedHostError


@pytest.mark.parametrize(
    "spelling",
    [
        "2130706433",     # decimal form of 127.0.0.1
        "0x7f000001",     # hex form of 127.0.0.1
        "0177.0.0.1",     # octal first octet
        "127.1",          # short dotted form of 127.0.0.1
    ],
)
def test_numeric_loopback_spellings_not_contacted(spelling):
    H.install()
    try:
        H.reset()
        # The transport resolves every one of these to 127.0.0.1.
        H.ROUTES["127.0.0.1"] = H.wire(200, "OK", {}, b"SECRET")
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("http://%s/admin" % spelling)
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()


def test_ipv6_loopback_literal_not_contacted():
    H.install()
    try:
        H.reset()
        H.DNS["::1"] = "::1"
        H.ROUTES["::1"] = H.wire(200, "OK", {}, b"SECRET")
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("http://[::1]/admin")
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()


def test_public_name_resolving_to_internal_not_contacted():
    H.install()
    try:
        H.reset()
        # A public-looking name that the resolver maps to a private address.
        H.DNS["assets.cdn-example.com"] = "10.0.0.5"
        H.ROUTES["10.0.0.5"] = H.wire(200, "OK", {}, b"SECRET")
        with pytest.raises(BlockedHostError):
            GuardedFetcher().fetch("http://assets.cdn-example.com/logo.png")
        assert H.contacted_internal() == [], H.CONTACTED
    finally:
        H.restore()
