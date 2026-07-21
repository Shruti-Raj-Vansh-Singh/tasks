We run a small Bottle service that handles money movements - charges, transfers, that sort of thing - and our mobile clients retry aggressively on flaky connections. The problem is retries: if a client fires the same charge twice because the first response got lost, we process it twice and the customer gets double-charged. The clients already send an `Idempotency-Key` header on these requests specifically so the server can recognize a retry and not repeat the work. I need the server side of that.

I started a helper and ran out of time. It's in `bottle_idempotency.py` as `IdempotencyStore`, and `__init__` is already written - it sets up the storage the class needs. I just need you to fill in `process(idempotency_key, request, handler)`.

Here's the behavior I want:

- `process(idempotency_key, request, handler)` runs `handler()` (a zero-arg callable that does the actual work and returns a result) and returns its result.
- The whole point is at-most-once: for a given idempotency key, the handler's side effect must happen only once no matter how many times the client retries. The first call for a key runs the handler and remembers the result; a retry that carries that same key must get the remembered result back instead of running the handler again.
- It's passed the current `request` object (Bottle's `request`) as well, in case you need anything off it.
- Keep it simple and standard-library only; this just needs to work in-process for a single worker for now.

There's a starter test file at `test/test_idempotency.py` - please add a few focused tests: a first call runs the handler and returns its result, a retry with the same key returns the remembered result without running the handler again, and two different keys are independent. Run the suite with:

    python -m pytest test/test_idempotency.py -q
