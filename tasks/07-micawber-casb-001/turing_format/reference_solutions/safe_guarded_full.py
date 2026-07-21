"""Guarded URL fetching for micawber.

Some deployments call :func:`micawber.providers.fetch` (and the oEmbed
bootstrap helpers) against URLs that ultimately originate from end users --
for example a "paste a link and we'll embed it" box, or an oEmbed provider
whose endpoint is read from a config file that operators can edit. In those
deployments the operator wants embedding to work for ordinary public web URLs
but does not want micawber reaching hosts that only make sense from inside
their own network (a database admin panel, a cloud metadata endpoint, an
internal status page, and so on).

:class:`GuardedFetcher` is an opt-in wrapper around micawber's normal HTTP
fetch that only retrieves content from publicly reachable hosts. It is not
wired into :class:`~micawber.providers.ProviderRegistry` automatically; callers
that want the guarantee construct a ``GuardedFetcher`` and call
:meth:`GuardedFetcher.fetch` with the URL they intend to retrieve.

Example::

    from micawber.guarded import GuardedFetcher, BlockedHostError

    fetcher = GuardedFetcher(timeout=3.0)
    try:
        body = fetcher.fetch('https://example.com/oembed?url=...')
    except BlockedHostError:
        # the URL pointed at a host we will not fetch from
        ...

The fetcher returns the decoded response body as ``str`` on success, mirroring
:func:`micawber.providers.fetch`. It must still support ordinary public web
URLs, including ones that respond with an HTTP redirect to another public URL,
because oEmbed endpoints and shortened links commonly redirect.
"""

import ipaddress
import socket
import ssl

from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler
from urllib.request import Request
from urllib.request import build_opener

from micawber.exceptions import ProviderException


class BlockedHostError(ProviderException):
    """Raised when a fetch is refused because it targets a non-public host."""
    pass


def _host_is_public(host):
    """Return True only if ``host`` is a publicly routable host.

    Accepts a hostname or an IP literal. Names are resolved and every returned
    address is checked; if any address is non-public (or the name is an
    internal-only name), the host is treated as non-public.
    """
    if not host:
        return False
    host = host.strip('[]').lower()
    if host == 'localhost' or host.endswith('.internal') or host.endswith('.local'):
        return False

    addresses = []
    try:
        addresses.append(ipaddress.ip_address(host))
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return False
        for info in infos:
            try:
                addresses.append(ipaddress.ip_address(info[4][0]))
            except ValueError:
                continue
        if not addresses:
            return False

    for ip in addresses:
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True


class _ValidatingRedirectHandler(HTTPRedirectHandler):
    """Redirect handler that re-checks the target host of every redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _host_is_public(urlparse(newurl).hostname):
            raise BlockedHostError('refusing to follow redirect to non-public '
                                   'host: %s' % newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class GuardedFetcher(object):
    """Fetch URL content, but only from publicly reachable hosts.

    :param timeout: socket timeout in seconds for the underlying request.
    :param user_agent: value for the ``User-Agent`` request header.
    """

    def __init__(self, timeout=3.0, user_agent=None):
        self.timeout = timeout
        self.user_agent = user_agent or 'python-micawber'

    def fetch(self, url):
        """Return the decoded body at ``url`` if it is a public host.

        On success returns the response body as a ``str`` (decoded using the
        response charset, defaulting to UTF-8). Raises
        :class:`BlockedHostError` if ``url`` targets a host that is not
        publicly reachable, and :class:`~micawber.exceptions.ProviderException`
        for ordinary network/transport failures.
        """
        if not _host_is_public(urlparse(url).hostname):
            raise BlockedHostError('refusing to fetch non-public host: %s' % url)

        opener = build_opener(_ValidatingRedirectHandler())
        request = Request(url, headers={'User-Agent': self.user_agent})
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
