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

Failure mode
------------

Code that only validates the caller-supplied URL and then hands it to a
transport that transparently follows redirects satisfies the rule for direct
requests but violates it under redirects: the initial public URL passes the
check, and the connection to the private redirect target is opened anyway. Such
code has *not* met this policy, even though it rejects a direct request to the
same private host.
