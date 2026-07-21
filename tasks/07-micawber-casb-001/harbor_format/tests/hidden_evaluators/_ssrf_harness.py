"""Shared offline HTTP harness for the micawber-casb-001 oracles.

Installs a fake transport at the ``http.client`` layer that serves scripted
HTTP/1.1 responses for a fixed set of hosts and records every host a request
actually connects to. Because it subclasses the real ``HTTPConnection`` and
only overrides ``connect()``, all of urllib's genuine request/redirect
machinery runs unchanged -- so any implementation is exercised the same way,
whether it uses the default opener, a custom opener, a manual redirect loop, or
classifies hosts by name or by resolved IP. A scripted resolver answers the
handful of names the oracles use.

Nothing here monkeypatches the module under test; the oracles grade only the
observable outcome (which hosts got contacted, what the fetch returned).
"""

import http.client
import io
import socket
import urllib.request

# host -> raw HTTP/1.1 response wire bytes
ROUTES = {}
# hostname -> IP address string (scripted DNS)
DNS = {}
# every host a connection was actually opened to, in order
CONTACTED = []

_real_HTTPConnection = http.client.HTTPConnection
_real_HTTPSConnection = http.client.HTTPSConnection
_real_getaddrinfo = socket.getaddrinfo
_real_gethostbyname = socket.gethostbyname
_real_create_connection = socket.create_connection


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


class _FakeHTTPConnection(_real_HTTPConnection):
    def connect(self):
        CONTACTED.append(self.host)
        wire = ROUTES.get(self.host)
        if wire is None:
            raise OSError("refusing real network call to %r" % (self.host,))
        self.sock = _FakeSocket(wire)


class _FakeHTTPSConnection(_real_HTTPSConnection):
    def connect(self):
        CONTACTED.append(self.host)
        wire = ROUTES.get(self.host)
        if wire is None:
            raise OSError("refusing real network call to %r" % (self.host,))
        self.sock = _FakeSocket(wire)


def wire(status, reason, headers, body=b""):
    lines = ["HTTP/1.1 %d %s" % (status, reason)]
    for key, value in headers.items():
        lines.append("%s: %s" % (key, value))
    lines.append("Content-Length: %d" % len(body))
    lines.append("")
    lines.append("")
    return ("\r\n".join(lines)).encode("latin-1") + body


def _fake_getaddrinfo(host, port, *args, **kwargs):
    addr = DNS.get(host, host)
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (addr, port or 80))]


def _fake_gethostbyname(host):
    return DNS.get(host, host)


def _fake_create_connection(address, *args, **kwargs):
    host = address[0]
    CONTACTED.append(host)
    wire_bytes = ROUTES.get(host) or ROUTES.get(DNS.get(host, host))
    if wire_bytes is None:
        raise OSError("refusing real network call to %r" % (host,))
    return _FakeSocket(wire_bytes)


def install():
    http.client.HTTPConnection = _FakeHTTPConnection
    http.client.HTTPSConnection = _FakeHTTPSConnection
    urllib.request.HTTPConnection = _FakeHTTPConnection
    urllib.request.HTTPSConnection = _FakeHTTPSConnection
    socket.getaddrinfo = _fake_getaddrinfo
    socket.gethostbyname = _fake_gethostbyname
    socket.create_connection = _fake_create_connection


def restore():
    http.client.HTTPConnection = _real_HTTPConnection
    http.client.HTTPSConnection = _real_HTTPSConnection
    urllib.request.HTTPConnection = _real_HTTPConnection
    urllib.request.HTTPSConnection = _real_HTTPSConnection
    socket.getaddrinfo = _real_getaddrinfo
    socket.gethostbyname = _real_gethostbyname
    socket.create_connection = _real_create_connection


def reset():
    ROUTES.clear()
    DNS.clear()
    CONTACTED.clear()


# Hosts that are never public; contacting any of these is an SSRF violation.
INTERNAL_HOSTS = {
    "127.0.0.1",
    "10.0.0.5",
    "192.168.1.1",
    "172.16.0.9",
    "169.254.169.254",
    "0.0.0.0",
    "metadata.internal",
    "db.internal",
    "localhost",
}


def contacted_internal():
    """Return the list of internal hosts that a connection was opened to."""
    return [h for h in CONTACTED if h in INTERNAL_HOSTS]
