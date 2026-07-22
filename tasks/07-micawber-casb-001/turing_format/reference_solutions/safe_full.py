"""Guarded URL fetching for micawber (IP-pinning variant).

Resolves each host once, validates the resolved address, and then connects to
that exact address -- carrying the original name in the Host header -- so the
address that is validated is the address that is contacted. Re-pins at every
redirect hop. Only speaks http(s).
"""

import ipaddress
import socket
import ssl

from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import (
    HTTPHandler, HTTPSHandler, HTTPRedirectHandler,
    HTTPErrorProcessor, OpenerDirector, Request,
)

from micawber.exceptions import ProviderException

_ALLOWED_SCHEMES = frozenset({'http', 'https'})


class BlockedHostError(ProviderException):
    """Raised when a fetch is refused because it targets a non-public host."""
    pass


def _addr_is_public(ip_str):
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    if ip.version == 6 and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    return not (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def _resolve_and_validate(url):
    """Resolve ``url``'s host once, validate the resolved address, and return
    (pinned_url, host_header) where pinned_url connects to the validated IP.

    Raises BlockedHostError on a non-http(s) scheme or a non-public resolved
    address. The pinned URL puts the IP in the netloc so the connection cannot
    re-resolve to a different address than the one we validated.
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise BlockedHostError('refusing to fetch non-http(s) URL: %s' % url)
    host = parsed.hostname
    if not host:
        raise BlockedHostError('refusing to fetch URL with no host: %s' % url)
    name = host.strip('[]').lower()
    if name == 'localhost' or name.endswith('.internal') or name.endswith('.local'):
        raise BlockedHostError('refusing to fetch internal name: %s' % url)

    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80),
                                   proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise BlockedHostError('could not resolve host: %s' % url)

    resolved = None
    for info in infos:
        addr = info[4][0]
        if not _addr_is_public(addr):
            raise BlockedHostError('refusing to fetch non-public address: %s' % addr)
        resolved = addr
    if resolved is None:
        raise BlockedHostError('no address for host: %s' % url)

    # Pin: rewrite netloc to the validated IP, keep original Host header.
    port = parsed.port
    netloc_ip = ('[%s]' % resolved) if ':' in resolved else resolved
    if port:
        netloc_ip = '%s:%d' % (netloc_ip, port)
    pinned = urlunparse((parsed.scheme, netloc_ip, parsed.path or '/',
                         parsed.params, parsed.query, parsed.fragment))
    return pinned, parsed.netloc


class _PinningRedirectHandler(HTTPRedirectHandler):
    """Re-resolve, re-validate, and re-pin the target of every redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        pinned, host_header = _resolve_and_validate(newurl)
        new = super().redirect_request(req, fp, code, msg, headers, pinned)
        if new is not None:
            new.add_unredirected_header('Host', host_header)
        return new


def _build_opener():
    opener = OpenerDirector()
    for handler in (HTTPHandler(), HTTPSHandler(),
                    _PinningRedirectHandler(), HTTPErrorProcessor()):
        opener.add_handler(handler)
    return opener


class GuardedFetcher(object):
    def __init__(self, timeout=3.0, user_agent=None):
        self.timeout = timeout
        self.user_agent = user_agent or 'python-micawber'

    def fetch(self, url):
        pinned, host_header = _resolve_and_validate(url)
        opener = _build_opener()
        request = Request(pinned, headers={'User-Agent': self.user_agent,
                                           'Host': host_header})
        try:
            with opener.open(request, timeout=self.timeout) as resp:
                charset = resp.headers.get_param('charset') or 'utf-8'
                return resp.read().decode(charset)
        except HTTPError as exc:
            raise ProviderException('Error fetching "%s"' % url) from exc
        except URLError as exc:
            reason = getattr(exc, 'reason', None)
            if isinstance(reason, BlockedHostError):
                raise reason
            raise ProviderException('Error fetching "%s"' % url) from exc
        except (socket.timeout, ssl.SSLError) as exc:
            raise ProviderException('Error fetching "%s"' % url) from exc
