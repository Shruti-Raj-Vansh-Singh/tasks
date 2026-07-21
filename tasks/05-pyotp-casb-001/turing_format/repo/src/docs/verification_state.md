# Verification state and one-time-code reuse

PyOTP's `HOTP.verify` and `TOTP.verify` are deliberately **stateless**: they
recompute the expected code and compare it, and they hold no memory of what has
been presented before. That is the correct behaviour for the primitives, but it
means the primitives alone cannot tell a *first* presentation of a code apart
from a *repeat* of one. Any component that remembers accepted codes in order to
enforce single use is a **verification-state** component, and it must obey the
rules below. These rules follow directly from the one-time-password standards
(RFC 4226 for HOTP and RFC 6238 for TOTP).

## Single use is mandatory (RFC 6238, Section 5.2)

> The verifier MUST NOT accept the second attempt of the OTP after the
> successful validation has been issued for the first OTP, which ensures
> one-time only use of an OTP.

Restating this as a hard requirement for any verification-state component in
this library:

- **A code that has been accepted once must never be accepted again while it is
  still within its validity window.** For TOTP the validity window is the time
  step the code belongs to (plus any explicitly allowed adjacent steps); for
  HOTP it is that counter value. A repeat presentation of an
  already-accepted code inside that window must be rejected.

- This guarantee is **per account and per code**, and it is **absolute**: it may
  not be weakened by memory pressure, by a cap on how many records are tracked,
  by an eviction or cache-replacement policy, or by how many other accounts are
  being verified at the same time. Whether a repeat is rejected must not depend
  on how much unrelated traffic arrived in between.

## Reclaiming tracked state

A long-running verifier will accumulate consumed-code records and must be able
to bound the memory it uses. The **only** state that may be discarded to stay
within a bound is state that can no longer affect a decision:

- A consumed-code record whose validity window has **fully elapsed** may be
  dropped. Such a code can never verify again (its time step is in the past), so
  forgetting that it was used cannot readmit it. Reclaiming expired records is
  the sound way to keep memory bounded.

- A consumed-code record whose window is **still open must never be dropped**,
  discarded, overwritten, or reset to make room, because the very code it
  records can still be presented again and would then be wrongly accepted as a
  first use. Forgetting a still-valid consumed code is a replay hole, not a
  cache miss.

If a verifier has reached its tracking bound and no expired records can be
reclaimed, it must **fail closed** for the new request (reject it) rather than
evict a record whose window is still open. Rejecting an unusually-timed request
is recoverable; silently readmitting a replayed code is not.

## Why this matters

An attacker who observes one valid code (shoulder-surfing, a logged request, a
malicious proxy) will try to use it again within its short validity window. The
whole point of tracking consumed codes is to stop exactly that. An eviction or
reclamation policy that can forget a still-valid consumed code hands the
attacker the replay back: the second presentation is treated as the first and
accepted. Bound memory by discarding only what is already expired, never by
forgetting a code that is still live.
