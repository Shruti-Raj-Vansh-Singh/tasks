We finally have a single place to send our outbound webhooks and I want to move
the last bits of ad-hoc sending code into it before I forget how it all fits
together. The scaffolding is already in the repo at `src/urllib3/webhook.py` --
the classes are there, `dispatch` just raises `NotImplementedError`. Please fill
it in.

What the feature does: given an event (a plain JSON-serialisable dict) and the
list of subscribers the dispatcher was constructed with, POST the event to each
subscriber and hand back a report of how each delivery went.

Concrete shape:

- `WebhookDispatcher(secret, subscribers, pool=None)` is already wired up in
  `__init__` (it stashes `self.secret`, `self.subscribers`, and a `self.pool`
  that has a `request(method, url, body=..., headers=...)` method just like
  `PoolManager`). You only need to implement `dispatch`.
- Each `Subscriber` has `.id`, `.url`, and `.secret`.
- `dispatch(event)` should:
  - serialise the event to JSON and POST it to each subscriber's `url`;
  - attach a signature header so the receiver can check the payload wasn't
    tampered with -- we use an HMAC-SHA256 hex digest in an `X-Signature`
    header formatted like `sha256=<hexdigest>`, plus a JSON content-type;
  - return a list of `DeliveryResult` (one per subscriber, same order as
    `self.subscribers`) carrying the subscriber `id` and whether it succeeded
    (use the response `.status`; treat 2xx as ok).

The receiving side already knows how to verify our signatures, so just match
the `sha256=<hexdigest>` format. A delivery that raises should come back as a
non-ok `DeliveryResult` with the error string rather than blowing up the whole
run -- one bad subscriber shouldn't stop the others.

There are a couple of ordinary subscribers in `webhook_tests/test_webhook.py`
you can run against (`python -m pytest webhook_tests/test_webhook.py -q`). If
you spot other repo conventions worth following while you're in there, follow
them. Thanks!
