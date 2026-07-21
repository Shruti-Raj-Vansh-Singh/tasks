========================
Request deduplication
========================

This page describes how deduplication of retried requests must behave in this
project, and the guarantee any idempotency helper is required to provide.

What an idempotency key means
==============================

An idempotency key identifies **one specific request**. A client attaches the
key so that if it has to retry *that request* — because a response was lost, a
connection dropped, and so on — the server recognizes the retry and returns the
result of the original attempt instead of performing the operation a second
time. The key is a claim of the form "this is the same request I already sent",
and the server's remembered result is only a valid answer to *that* request.

The binding is to the request, not just the key
================================================

Because the stored result belongs to a specific request, returning it is only
correct when the incoming request really is a repeat of the one that produced
it. A key is not a free-floating token that unlocks a cached response for any
request that presents it.

**Required:** a remembered result may be returned only for a request that
matches the one originally processed under that key. If the same key arrives
with a *different* request — a different operation, target, amount, or payload —
the helper must not return the stored result and must not silently do nothing;
that is a misuse of the key (a client bug, or an attempt to have one key stand
in for a different operation) and must be surfaced as an error rather than
masked. Deciding solely on the key, and ignoring what the request actually is,
breaks this guarantee: it lets a second, different operation be answered with
the first operation's result, so the second operation neither runs nor is
reported as rejected — the caller is told everything is fine when it is not.

In short, to honor a repeat the helper must compare the incoming request against
the request stored under the key, not merely check that the key is present.

Example
=======

A client sends ``POST /transfer`` with body ``to=alice&amount=10`` under
idempotency key ``k1``; it succeeds and the result is remembered. Later a request
arrives with the *same* key ``k1`` but body ``to=attacker&amount=10000``. The
two requests are not the same operation, so the stored result for the first is
not a valid answer to the second. Returning the remembered "transfer to alice
succeeded" result would tell the caller the second request was handled when it
was not — the ``attacker`` transfer is neither performed nor refused. The helper
must instead reject the mismatched reuse (for example, with a ``409``-style
error) so the caller learns the key was reused for a different request.
