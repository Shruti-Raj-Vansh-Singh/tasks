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

from micawber.exceptions import ProviderException


class BlockedHostError(ProviderException):
    """Raised when a fetch is refused because it targets a non-public host."""
    pass


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
        raise NotImplementedError('GuardedFetcher.fetch is not implemented yet')
