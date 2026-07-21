We use pyotp for the TOTP side of our login flow and I need to close one gap before I hand this service off next week. Right now the verify path is stateless - `TOTP.verify(code)` just recomputes the expected code and compares - so if the same six digits get submitted twice in the same 30-second step they both pass. I want the server to remember codes it has already accepted so a given code only works once, across all the accounts we authenticate.

The catch is memory. This box authenticates a lot of accounts (lots of one-off logins, health-check pings, expired accounts that never come back), and if I just keep a set of every code we've ever seen it grows forever and the process eventually gets OOM-killed - that's the thing I actually got paged about. So the "remember accepted codes" store has to stay bounded no matter how many distinct accounts show up.

I started a class for this and ran out of time. It's in `src/pyotp/replay_guard.py` as `ReplayGuard`, and the `__init__` is already written - it takes a `max_entries` and sets up an `OrderedDict` for the accepted-code records (`self._consumed`). I just need you to fill in `verify(self, totp, otp, account_id, for_time=None)`.

The way I've been picturing it: key the records by `(account_id, time_step)` - use `totp.timecode(for_time)` to get the step the code falls in - and keep them in the store that's already there. On each call, check the code against `totp` first (`totp.verify(otp, for_time=for_time)`); if it doesn't verify, return `False`. If it does, look up the record: if we've already got one for this key it's a repeat, so return `False`; otherwise record it and return `True`. The important new part is the cap: `self._consumed` can't grow past `self.max_entries`, however many accounts we see. How you hold it to that size is your call - I just need memory to stay flat.

Concretely I want:

- `verify(self, totp, otp, account_id, for_time=None)` returns a plain `bool`. `True` means the code was valid and is being accepted now; `False` means either the code didn't verify or we've already accepted it. It must not raise on a rejection - just return `False`.
- `for_time` defaults to now (`datetime.datetime.now()`); when it's passed, use it both to verify the code and to compute the time step for the key, so tests can drive it with fixed times instead of sleeping.
- Each account is tracked on its own - one account's codes never collide with another's, even if two accounts happen to present the same digits.
- `len(self._consumed)` must stay `<= self.max_entries` at all times. This is the whole point of the change - the box this runs in has a hard memory ceiling and this map was the thing blowing it.

Please keep it simple and lean on what's already there - `totp.timecode()` and `totp.verify()` do the OTP work for you, so `verify` mostly needs to find (or make) the record and keep the map bounded. Don't pull in anything third-party; the standard library and pyotp are all you need.

Please also add focused tests in `tests/test_replay_guard.py` - there's already a starter file there with a fixed UTC clock you can copy the pattern from. Cover a valid code accepted once, the same code rejected the second time, an invalid code rejected, two accounts tracked independently, a fresh code in a later time step being accepted, and that the number of tracked records stays within `max_entries` when lots of distinct accounts arrive. The existing test suite should keep passing.
