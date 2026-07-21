State Management
================

Some deployments keep a small amount of server-side state alongside the
stateless signatures that itsdangerous produces - for example a record of which
tokens have been retired early, a set of identifiers that have already been
seen, or per-recipient bookkeeping. This page states the guarantees such
server-side state must uphold so that adding it never weakens the security
decision the signature layer already makes.

Decisions must not depend on retained memory
--------------------------------------------

A signed token carries its own validity: the signature proves integrity and the
embedded timestamp bounds its lifetime. Any server-side state kept on the side
is there to make a decision **more** restrictive (retiring a token early,
rejecting something already seen), never less. From this the following rule
follows and **must** hold:

    Discarding a piece of server-side state must never change a decision from
    "reject" to "accept". If a token would be rejected while the state is
    retained, it must still be rejected after the state is discarded.

Concretely, once the system has decided that a particular token is no longer
acceptable - because it was retired early, or already used, or otherwise
recorded as not-to-be-honored - that decision **must** hold for the entire
remainder of the token's validity window. It must not matter how much other
traffic arrived in between, how many other tokens were recorded, or whether the
process chose to drop bookkeeping to save memory. A token that has been marked
unacceptable stays unacceptable until it would expire on its own.

Bounding memory safely
----------------------

Long-running services cannot let this side state grow without limit, so it is
correct - and expected - to reclaim it. The rule above constrains *which* state
may be reclaimed:

- **Safe to drop:** state for a token whose ``max_age`` window has already
  elapsed. Such a token is rejected by the timestamp check regardless, so
  forgetting the extra state changes no decision.

- **Never safe to drop:** state for a token that is still inside its validity
  window and whose retained state is what makes it unacceptable. Dropping that
  entry to make room - for instance by evicting the oldest entry when a size cap
  is hit - silently readmits a token that the service had already decided to
  reject. That is a security regression even though the code "still enforces a
  bound".

If memory pressure means the only way to stay within a size cap would be to drop
live, still-relevant state, the correct behavior is to preserve the safety
decision (keep rejecting) rather than to reclaim the entry. Reclaim on
expiry, not on recency.

Example
-------

Suppose a token is valid for one hour and is retired early after ten minutes.
For the remaining fifty minutes, any check of that token must report it as not
acceptable - even if, in that window, thousands of other tokens are issued and
retired and the service is holding only a bounded amount of state. Evicting the
retired token's record early because "it was the oldest" and then accepting the
token again is exactly the regression this rule forbids.
