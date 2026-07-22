Outbound delivery policy
========================

This page records the rules every outbound-request feature in this project must
follow. It applies to any code that sends HTTP requests to endpoints that
originate outside the application -- subscriber callbacks, user-configured
destinations, imported target lists, and similar -- and to the payloads those
requests carry.

.. _delivery-destinations:

Permitted destinations
-----------------------

A request produced from an externally supplied destination may target only a
routable, external ``http`` or ``https`` endpoint. Such a request must never be
issued to:

* any scheme other than ``http``/``https`` (``file:``, ``gopher:``, ``ftp:``,
  and so on);
* loopback addresses (``127.0.0.0/8``, ``::1``) or the name ``localhost``;
* link-local addresses (``169.254.0.0/16``, ``fe80::/10``), which include the
  cloud instance-metadata endpoint ``169.254.169.254``;
* private ranges (``10.0.0.0/8``, ``172.16.0.0/12``, ``192.168.0.0/16``,
  ``fc00::/7``) and other reserved, unspecified, or multicast ranges.

A destination that cannot be shown to be external must be refused, not
attempted.

.. _delivery-redirects:

Redirects
---------

A redirect response must not be followed to a new location unless that location
also satisfies :ref:`delivery-destinations`. A destination that was acceptable
when it was registered can still redirect a request to an internal address, so
following redirects blindly re-opens exactly the exposure the destination check
was there to close. Either do not follow redirects for these requests, or
re-check each hop's location against the destination rule before following it.

.. _delivery-signing:

Per-recipient signing
---------------------

When a request is signed on behalf of a registered recipient, it must be signed
with **that recipient's own credential**. Each subscription record carries its
own ``secret``; the signature attached to a delivery for a given subscriber is
computed with that subscriber's ``secret`` and no other. A shared or
application-wide key must never be used to sign a per-recipient delivery -- a
signature is a per-recipient credential, and reusing one credential across
recipients lets any one recipient forge or validate messages meant for another.

Application-level credentials -- pool default headers such as ``Authorization``,
service tokens, and the like -- must not be attached to requests sent to these
external endpoints.

.. _delivery-payload:

Payload minimisation
--------------------

A payload sent to an external endpoint must contain only the fields that are
meant to leave our trust boundary. Internal event records routinely carry
fields that are for internal use only -- contact details and other personal
data, internal identifiers, operator notes, and similar. Before an event is
sent outward it must be reduced to the agreed public projection (event type,
public id, and the public ``data`` block); internal and personal fields are
dropped. Do not serialise an internal record verbatim onto the wire.
