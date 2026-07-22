"""Shared offline HTTP harness for the micawber-casb-001 oracles.

Installs a fake transport at the ``http.client`` layer that serves scripted
HTTP/1.1 responses for a fixed set of hosts and records every host a request
actually connects to. Because it subclasses the real ``HTTPConnection`` and
only overrides ``connect()``, all of urllib's genuine request/redirect
machinery runs unchanged -- so any implementation is exercised the same way,
whether it uses the default opener, a custom opener, a manual redirect loop, or
classifies hosts by name or by resolved IP. A scripted resolver answers the
handful of names the oracles use.

Every connection records BOTH the literal host string the transport was asked
to reach AND the address that host resolves to under the scripted resolver, so
a host that is written to look public but resolves to an internal address (a
public-looking name mapped to a private IP, or a decimal/octal/hex/IPv6
spelling of an internal address) is still observed as a contact to the internal
address. A file:// or data: read touches no socket, so those are tracked
separately via ``LOCAL_READS``.

Nothing here monkeypatches the module under test; the oracles grade only the
observable outcome (which hosts got contacted, whether a local resource was
opened, what the fetch returned).
"""

import http.client
import io
import socket
import urllib.request

# host -> raw HTTP/1.1 response wire bytes
ROUTES = {}
# hostname (or numeric spelling) -> IP address string (scripted DNS)
DNS = {}
# hostname -> (first_answer, subsequent_answer): a name whose resolution CHANGES
# between the first lookup and later lookups, modelling a DNS-rebinding server
# that answers a public address to a validating lookup and a private address to
# the connection's own lookup. The per-name lookup counter is kept here so the
# split is observed identically by a guard's validating resolve and by the
# transport's connect-time resolve (both go through ``_resolve``).
REBIND = {}
_REBIND_CALLS = {}
# every host a connection was actually opened to, in order. Contains BOTH the
# literal host the transport was handed and the address it resolved to.
CONTACTED = []
# every local resource (file:// path, data: url) that was actually opened.
LOCAL_READS = []

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


def _resolve(host):
    """Return the scripted address ``host`` resolves to (glibc-style).

    A name in ``REBIND`` resolves to its first answer on the first lookup and to
    its second answer on every later lookup, modelling a rebinding server. The
    counter is shared across all callers, so a guard that resolves a name to
    validate it and then lets the transport resolve the same name to connect
    sees the address change between the two -- exactly as it would against a real
    rebinding DNS server. Other names and IPv6 literals resolve through the
    ``DNS`` table (defaulting to the host itself). Numeric IPv4 spellings --
    decimal, octal, hex, and short dotted forms such as ``2130706433`` /
    ``0177.0.0.1`` / ``127.1`` -- are normalized with ``inet_aton`` exactly as
    the platform resolver would, so an internal address written in an unusual
    base is still resolved to its canonical dotted form.
    """
    if host in REBIND:
        n = _REBIND_CALLS.get(host, 0)
        _REBIND_CALLS[host] = n + 1
        first, later = REBIND[host]
        return first if n == 0 else later
    if host in DNS:
        return DNS[host]
    try:
        return socket.inet_ntoa(_real_gethostbyname_aton(host))
    except OSError:
        return host


def _real_gethostbyname_aton(host):
    # inet_aton accepts the numeric spellings glibc's resolver also accepts.
    return socket.inet_aton(host)


def _connect_to(host):
    """Resolve ``host`` exactly once, record the contact to both the literal
    host and the address it resolved to, and return the wire bytes for whatever
    is at that address (or ``None`` if nothing is routed there).

    Resolving exactly once per connection is essential for the rebinding
    scenarios: the address the connection is recorded as reaching MUST be the
    same address whose route is served, otherwise a fetcher that lets the
    transport re-resolve a rebinding name would be recorded as contacting the
    validated (public) address while actually being served the private body.
    """
    resolved = _resolve(host)
    CONTACTED.append(host)
    if resolved != host:
        CONTACTED.append(resolved)
    return ROUTES.get(host) or ROUTES.get(resolved)


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


def wire(status, reason, headers, body=b""):
    lines = ["HTTP/1.1 %d %s" % (status, reason)]
    for key, value in headers.items():
        lines.append("%s: %s" % (key, value))
    lines.append("Content-Length: %d" % len(body))
    lines.append("")
    lines.append("")
    return ("\r\n".join(lines)).encode("latin-1") + body


def _fake_getaddrinfo(host, port, *args, **kwargs):
    addr = _resolve(host)
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (addr, port or 80))]


def _fake_gethostbyname(host):
    return _resolve(host)


def _fake_create_connection(address, *args, **kwargs):
    host = address[0]
    wire_bytes = _connect_to(host)
    if wire_bytes is None:
        raise OSError("refusing real network call to %r" % (host,))
    return _FakeSocket(wire_bytes)


# --- file:// and data: transports (socket-invisible) ------------------------
# urllib's FileHandler/DataHandler never touch a socket, so a fetch of a local
# resource cannot be observed via CONTACTED. We install thin file-scheme and
# data-scheme openers on the module under test's behalf by intercepting the
# stdlib's local-file opener. A fetcher that restricts itself to http/https
# never triggers these; one that hands an arbitrary scheme to a default opener
# does, and the read is recorded in LOCAL_READS.
_real_open_local_file = urllib.request.URLopener.open_local_file \
    if hasattr(urllib.request, "URLopener") else None

_LOCAL_FILES = {}  # "/etc/passwd" -> b"root:x:0:0:..."


def _fake_file_open(self, req):
    # Mirrors urllib.request.FileHandler.file_open closely enough to satisfy a
    # naive fetcher, while recording the access and never touching the disk.
    import email.utils
    from urllib.parse import urlparse
    from urllib.response import addinfourl
    path = urlparse(req.full_url).path
    LOCAL_READS.append(path)
    data = _LOCAL_FILES.get(path, b"LOCAL-FILE-CONTENTS")
    headers = http.client.HTTPMessage()
    headers["Content-Type"] = "text/plain"
    headers["Content-Length"] = str(len(data))
    return addinfourl(io.BytesIO(data), headers, req.full_url)


_real_file_open = urllib.request.FileHandler.file_open


def install():
    http.client.HTTPConnection = _FakeHTTPConnection
    http.client.HTTPSConnection = _FakeHTTPSConnection
    urllib.request.HTTPConnection = _FakeHTTPConnection
    urllib.request.HTTPSConnection = _FakeHTTPSConnection
    socket.getaddrinfo = _fake_getaddrinfo
    socket.gethostbyname = _fake_gethostbyname
    socket.create_connection = _fake_create_connection
    urllib.request.FileHandler.file_open = _fake_file_open


def restore():
    http.client.HTTPConnection = _real_HTTPConnection
    http.client.HTTPSConnection = _real_HTTPSConnection
    urllib.request.HTTPConnection = _real_HTTPConnection
    urllib.request.HTTPSConnection = _real_HTTPSConnection
    socket.getaddrinfo = _real_getaddrinfo
    socket.gethostbyname = _real_gethostbyname
    socket.create_connection = _real_create_connection
    urllib.request.FileHandler.file_open = _real_file_open


def reset():
    ROUTES.clear()
    DNS.clear()
    REBIND.clear()
    _REBIND_CALLS.clear()
    CONTACTED.clear()
    LOCAL_READS.clear()
    _LOCAL_FILES.clear()


def set_local_file(path, contents):
    _LOCAL_FILES[path] = contents


def set_rebind(host, first_addr, later_addr):
    """Make ``host`` resolve to ``first_addr`` on the first lookup and
    ``later_addr`` on every later lookup (a rebinding DNS server)."""
    REBIND[host] = (first_addr, later_addr)
    _REBIND_CALLS.pop(host, None)


# Hosts that are never public; contacting any of these is an SSRF violation.
# Includes canonical internal addresses AND the identities the alternate-encoding
# and DNS-rebinding scenarios resolve to (every one of these ends up as one of
# these literals after _resolve()).
INTERNAL_HOSTS = {
    "127.0.0.1",
    "10.0.0.5",
    "192.168.1.1",
    "172.16.0.9",
    "169.254.169.254",
    "0.0.0.0",
    "::1",
    "metadata.internal",
    "db.internal",
    "localhost",
}


def contacted_internal():
    """Return the list of internal identities a connection was opened to.

    Because ``CONTACTED`` records both the literal host and its resolved
    address, an internal address reached under a public-looking name or an
    unusual numeric spelling still shows up here.
    """
    return [h for h in CONTACTED if h in INTERNAL_HOSTS]
