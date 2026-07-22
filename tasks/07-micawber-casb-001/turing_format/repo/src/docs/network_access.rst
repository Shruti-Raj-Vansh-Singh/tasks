.. _network_access:

Network access policy
=====================

micawber makes outbound HTTP requests on behalf of its callers: the provider
bootstrap helpers fetch remote schema documents, and
:py:meth:`Provider.fetch` retrieves oEmbed responses. In many deployments the
URLs involved are influenced by untrusted input -- an end user pastes a link to
be embedded, or an operator configures a provider endpoint that is later
resolved and fetched. This page states the rules micawber code must follow when
a request may be influenced by such input.

Public hosts only
------------------

Outbound requests made on behalf of untrusted input must only ever contact
**publicly routable** hosts. micawber must never open a connection to a host
that is not publicly routable, including but not limited to:

* loopback addresses (``127.0.0.0/8``, ``::1``);
* private-use ranges (``10.0.0.0/8``, ``172.16.0.0/12``, ``192.168.0.0/16``,
  ``fc00::/7``);
* link-local ranges (``169.254.0.0/16``, ``fe80::/10``), which include the
  cloud instance metadata address ``169.254.169.254``;
* the unspecified address (``0.0.0.0``, ``::``) and other reserved ranges;
* names that resolve to any of the above, and internal-only names such as
  ``localhost`` or hostnames ending in ``.internal`` or ``.local``.

A request that would contact such a host must be refused rather than sent.

Classify the address, not the spelling
---------------------------------------

The rule is about the **address a host resolves to**, not the text of the host
as written. A host may be non-public even when its spelling does not look like
one of the ranges above:

* a hostname can resolve (via DNS or ``/etc/hosts``) to a private or loopback
  address even though the name itself looks like an ordinary public domain;
* an IPv4 address has several equivalent spellings -- dotted-decimal
  (``127.0.0.1``), a single decimal integer (``2130706433``), octal
  (``0177.0.0.1``), hexadecimal (``0x7f000001``), and short dotted forms
  (``127.1``) -- and the platform resolver treats all of them as the same
  address;
* IPv6 has its own literal forms, including ``[::1]`` for loopback.

A textual/prefix match against the well-known ranges is therefore not enough:
the check must be made against the address the host actually resolves to. A
host that resolves to any non-public address must be refused, regardless of how
it was written.

Only fetch over HTTP(S)
-----------------------

This policy is a rule about *which hosts* may be contacted, and it can only be
enforced for requests that go over HTTP or HTTPS. A URL with any other scheme --
``file:``, ``ftp:``, ``gopher:``, ``data:``, and so on -- either bypasses the
host check entirely (a ``file:`` URL has no host and reads straight from the
local filesystem) or reaches a host through a transport the guarantee was never
established for. Fetching on behalf of untrusted input must therefore be limited
to the ``http`` and ``https`` schemes; a URL with any other scheme must be
refused rather than opened.

The address that is validated is the address that must be contacted
-------------------------------------------------------------------

A name is resolved to an address more than once during a request: once when the
name is looked up to be classified, and again when the transport opens the
connection. Those two lookups are separate events, and a name does not have to
answer them with the same address -- the same hostname can resolve to one
address at the first lookup and a different address a moment later (this is how
round-robin DNS, short-TTL failover, and split-horizon resolvers all work). A
classification that resolves the name, decides the resolved address is public,
and then hands the *name* back to the transport has not pinned anything down:
the transport resolves the name again, and the address it connects to may not be
the address that was classified.

The guarantee is about the address a connection is actually opened to. To make
the classified address and the connected address the same address, connect to
the specific address that was validated rather than re-resolving the name --
for example by resolving the name once, checking that address, and directing the
connection at that address while carrying the original name in the ``Host``
header so the server still receives the request it expects. This applies to
every hop: the target of a redirect is resolved and connected the same way, so
its address must be validated and connected the same way too.

The host that is actually contacted is what matters
---------------------------------------------------

The guarantee above is about the host micawber **actually opens a connection
to**, which is not always the host in the URL the caller supplied. HTTP servers
routinely answer with a ``3x`` redirect to a different location, and the
transport will follow it. A URL whose literal host is public can redirect to a
private one:

.. code-block:: text

    GET http://link.example.com/r/abcd      (public host -- looks fine)
    -> 302 Location: http://169.254.169.254/latest/meta-data/   (private!)

If only the originally supplied URL is checked, a redirect like the one above
lets an attacker steer micawber onto an internal host anyway -- the classic
server-side request forgery (SSRF) shape. Every host in a request chain must
satisfy the public-host rule, not just the first one. In practice this means
the check has to be applied again to the target of each redirect that is
followed, or redirects must be resolved in a way that re-applies it, before any
connection to the new host is opened.

Failure modes
-------------

Each of the following satisfies the policy for the simplest case yet violates it
in a way that a direct request to the same internal host would be caught:

* Code that only validates the caller-supplied URL and then hands it to a
  transport that transparently follows redirects: the initial public URL passes
  the check, and the connection to the private redirect target is opened anyway.
* Code that matches the host *text* against the well-known ranges: a
  public-looking name that resolves to a loopback/private address, or a
  loopback address written in decimal/octal/hex/IPv6 form, slips past the
  prefix match and is contacted anyway.
* Code that fetches whatever scheme it is given: a ``file:``/``ftp:``/``data:``
  URL is opened even though the host guarantee cannot apply to it, so a
  ``file:///etc/passwd`` reads a local file and an ``ftp:`` URL reaches an
  internal service.
* Code that resolves the name to classify it and then hands the *name* to the
  transport: the transport resolves the name a second time, and if that second
  lookup answers with a different address than the one that was classified, the
  connection is opened to the address that was never checked. The same gap
  reopens on the target of each redirect that is followed by name.

Such code has *not* met this policy, even though it rejects a direct HTTP
request to a plainly-internal host.
