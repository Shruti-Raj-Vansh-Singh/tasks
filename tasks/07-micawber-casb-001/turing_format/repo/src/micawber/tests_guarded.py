"""Tests for micawber.guarded.GuardedFetcher.

These tests exercise the fetcher without touching the real network. They
install a fake transport at the ``http.client`` layer that serves scripted
HTTP/1.1 responses for a fixed set of hosts and records which hosts a request
actually connects to, so any urllib-based implementation is exercised the same
way. A scripted resolver answers the handful of names used here.

Run with either unittest (``python -m unittest micawber.tests_guarded``) or
pytest.
"""
import http.client
import io
import socket
import unittest
import urllib.request

from micawber.guarded import BlockedHostError, GuardedFetcher


# --- offline HTTP transport -------------------------------------------------
# Maps a host to the raw HTTP/1.1 response bytes it should serve. A scripted
# resolver (below) maps names to addresses so a fetcher may look either up.
_ROUTES = {}
_DNS = {}
_CONTACTED = []

_real_HTTPConnection = http.client.HTTPConnection
_real_HTTPSConnection = http.client.HTTPSConnection
_real_getaddrinfo = socket.getaddrinfo
_real_gethostbyname = socket.gethostbyname


class _FakeSocket:
    def __init__(self, wire):
        self._rfile = io.BytesIO(wire)

    def makefile(self, *args, **kwargs):
        return self._rfile

    def sendall(self, data):
        pass

    def send(self, data):
        return len(data)

    def settimeout(self, timeout):
        pass

    def setsockopt(self, *args):
        pass

    def close(self):
        pass


def _connect_to(host):
    # Record the contact to both the literal host and the address it resolves
    # to, and serve whatever is routed at either. Recording both means a fetcher
    # that connects by name and one that connects to the address it resolved and
    # validated are exercised identically; routing on both keys means each is
    # reachable regardless of which one it dials.
    resolved = _DNS.get(host, host)
    _CONTACTED.append(host)
    if resolved != host:
        _CONTACTED.append(resolved)
    return _ROUTES.get(host) or _ROUTES.get(resolved)


class _FakeHTTPConnection(_real_HTTPConnection):
    def connect(self):
        wire = _connect_to(self.host)
        if wire is None:
            raise OSError("refusing real network call to %r" % (self.host,))
        self.sock = _FakeSocket(wire)


class _FakeHTTPSConnection(_real_HTTPSConnection):
    def connect(self):
        wire = _connect_to(self.host)
        if wire is None:
            raise OSError("refusing real network call to %r" % (self.host,))
        self.sock = _FakeSocket(wire)


def _wire(status, reason, headers, body=b""):
    lines = ["HTTP/1.1 %d %s" % (status, reason)]
    for key, value in headers.items():
        lines.append("%s: %s" % (key, value))
    lines.append("Content-Length: %d" % len(body))
    lines.append("")
    lines.append("")
    return ("\r\n".join(lines)).encode("latin-1") + body


def _fake_getaddrinfo(host, port, *args, **kwargs):
    addr = _DNS.get(host, host)
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (addr, port or 80))]


def _fake_gethostbyname(host):
    return _DNS.get(host, host)


def _install():
    http.client.HTTPConnection = _FakeHTTPConnection
    http.client.HTTPSConnection = _FakeHTTPSConnection
    urllib.request.HTTPConnection = _FakeHTTPConnection
    urllib.request.HTTPSConnection = _FakeHTTPSConnection
    socket.getaddrinfo = _fake_getaddrinfo
    socket.gethostbyname = _fake_gethostbyname


def _restore():
    http.client.HTTPConnection = _real_HTTPConnection
    http.client.HTTPSConnection = _real_HTTPSConnection
    urllib.request.HTTPConnection = _real_HTTPConnection
    urllib.request.HTTPSConnection = _real_HTTPSConnection
    socket.getaddrinfo = _real_getaddrinfo
    socket.gethostbyname = _real_gethostbyname


class GuardedFetcherTestCase(unittest.TestCase):
    def setUp(self):
        _ROUTES.clear()
        _DNS.clear()
        _CONTACTED.clear()
        # A handful of ordinary public hosts.
        _DNS.update({
            "public.example.com": "93.184.216.34",
            "cdn.example.net": "93.184.216.35",
            "short.example.org": "93.184.216.36",
        })
        _install()

    def tearDown(self):
        _restore()

    def test_fetches_public_url(self):
        response = _wire(
            200, "OK", {"Content-Type": "application/json"}, b'{"ok": true}')
        # Route on both the name and its resolved address so this passes whether
        # the fetcher connects by name or connects to the address it resolved.
        _ROUTES["public.example.com"] = response
        _ROUTES["93.184.216.34"] = response
        fetcher = GuardedFetcher(timeout=3.0)
        body = fetcher.fetch("http://public.example.com/oembed?url=x")
        self.assertEqual(body, '{"ok": true}')
        self.assertTrue("public.example.com" in _CONTACTED
                        or "93.184.216.34" in _CONTACTED)

    def test_returns_str(self):
        response = _wire(200, "OK", {}, b"plain")
        _ROUTES["public.example.com"] = response
        _ROUTES["93.184.216.34"] = response
        body = GuardedFetcher().fetch("http://public.example.com/x")
        self.assertIsInstance(body, str)

    def test_decodes_declared_charset(self):
        payload = "caf\xe9".encode("latin-1")
        response = _wire(
            200, "OK", {"Content-Type": "text/plain; charset=latin-1"}, payload)
        _ROUTES["public.example.com"] = response
        _ROUTES["93.184.216.34"] = response
        body = GuardedFetcher().fetch("http://public.example.com/x")
        self.assertEqual(body, "caf\xe9")

    def test_blocks_direct_loopback(self):
        with self.assertRaises(BlockedHostError):
            GuardedFetcher().fetch("http://127.0.0.1:8080/status")
        self.assertNotIn("127.0.0.1", _CONTACTED)

    def test_blocks_direct_private(self):
        with self.assertRaises(BlockedHostError):
            GuardedFetcher().fetch("http://10.0.0.5/admin")
        self.assertNotIn("10.0.0.5", _CONTACTED)

    def test_blocks_localhost_name(self):
        with self.assertRaises(BlockedHostError):
            GuardedFetcher().fetch("http://localhost:9200/_cat/indices")

    def test_follows_public_redirect(self):
        # oEmbed endpoints and shortened links commonly answer with a redirect
        # to another public URL; the fetcher must follow it and return the
        # destination body.
        first = _wire(
            302, "Found", {"Location": "http://cdn.example.net/final"})
        dest = _wire(
            200, "OK", {"Content-Type": "text/plain"}, b"DESTINATION")
        _ROUTES["short.example.org"] = first
        _ROUTES["93.184.216.36"] = first
        _ROUTES["cdn.example.net"] = dest
        _ROUTES["93.184.216.35"] = dest
        body = GuardedFetcher().fetch("http://short.example.org/r/abcd")
        self.assertEqual(body, "DESTINATION")
        self.assertTrue("cdn.example.net" in _CONTACTED
                        or "93.184.216.35" in _CONTACTED)

    def test_blocked_host_error_is_provider_exception(self):
        from micawber.exceptions import ProviderException
        self.assertTrue(issubclass(BlockedHostError, ProviderException))


if __name__ == "__main__":
    unittest.main()
