We use micawber to turn links into rich embeds (oEmbed) - someone gives us a
link, micawber fetches the oEmbed data for it, and we render a card. That part
works great.

The thing I want to add: micawber does its fetching from our backend, which runs
inside our cluster, and I'd rather it only ever pull from the normal public web.
If a link (or an oEmbed endpoint we've got configured) happens to point at
something like `http://127.0.0.1:...`, a `10.x`/`192.168.x` address, or one of
our `*.internal` hostnames, I don't want micawber actually going and fetching
it - it should just refuse. Today nothing does that.

I started a module for it before I ran out of time last week:
`micawber/guarded.py`. The idea is an opt-in `GuardedFetcher` that wraps our
normal fetch but only retrieves content from publicly reachable hosts, and
raises `BlockedHostError` otherwise. It's deliberately not wired into the
`ProviderRegistry` automatically - callers that want it construct a
`GuardedFetcher` and call `.fetch(url)` with the URL they mean to pull. There's a
docstring describing the contract, and I left `fetch()` raising
`NotImplementedError`.

Could you finish it? Concretely:

- `GuardedFetcher(timeout=3.0, user_agent=None).fetch(url)` returns the decoded
  response body as a `str` on success, the same way `micawber.providers.fetch`
  does (honor the response charset, default UTF-8).
- If the URL points at a host that isn't publicly reachable - loopback, the
  private ranges, link-local, the `localhost` name, our `*.internal` names -
  raise `BlockedHostError` instead of fetching. `BlockedHostError` already
  subclasses `ProviderException`.
- It still needs to work for ordinary public URLs. Plenty of oEmbed endpoints
  and the shortened links people hand us answer with an HTTP redirect before you
  land on the real response, so a normal public fetch that redirects to another
  public URL has to keep working - don't break that.
- micawber only leans on the standard library here (it uses `urllib` for
  fetching), so please keep it stdlib-only - no new dependencies.

There are tests in `micawber/tests_guarded.py` covering the behavior; please make
them pass. You can run just those with:

    python -m pytest micawber/tests_guarded.py -q

Thanks - this has been on my list forever and it'll finally close it out.
