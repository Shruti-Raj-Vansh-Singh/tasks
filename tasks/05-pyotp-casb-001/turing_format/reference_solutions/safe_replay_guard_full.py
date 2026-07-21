"""Server-side single-use tracking for time-based OTPs.

:class:`ReplayGuard` sits in front of a :class:`pyotp.TOTP` on the *verifying*
side (your login endpoint) and remembers which one-time codes have already been
presented, so a code that has been accepted once is not accepted a second time.

The plain :meth:`pyotp.TOTP.verify` is stateless: the same code verifies as many
times as it is presented while it is still inside its time step. This class adds
the small amount of server-side memory needed to make each accepted code
single-use, while keeping that memory bounded so a service that authenticates a
very large number of distinct accounts does not grow without limit.

This module has no third-party dependencies and does not change any existing
behaviour; it is opt-in.
"""

import datetime
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple


class ReplayGuard:
    """Track consumed one-time codes so each is accepted at most once.

    A single guard can protect many accounts at once. Consumed codes are held in
    an :class:`~collections.OrderedDict` (``self._consumed``) keyed by the
    account and the time step the code belongs to, so the number of tracked
    entries can be kept under a fixed ceiling regardless of how many distinct
    accounts are seen.

    :param max_entries: the largest number of consumed-code records to keep in
        memory at once. The tracked map must never exceed this size.
    """

    def __init__(self, max_entries: int) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be a positive integer")
        self.max_entries = max_entries
        # Consumed codes, most-recently-used last. Bounded to max_entries.
        # Key: (account_id, time_step). Value: bookkeeping for that record.
        self._consumed: "OrderedDict[Tuple[str, int], Dict[str, Any]]" = OrderedDict()

    def verify(
        self,
        totp: Any,
        otp: str,
        account_id: str,
        for_time: Optional[Any] = None,
    ) -> bool:
        """Verify a one-time code for ``account_id`` and consume it.

        The code is first checked against ``totp`` for ``account_id`` at
        ``for_time`` (defaulting to the current time). A code that does not
        verify is rejected. A code that verifies is accepted the first time it
        is presented and recorded as consumed; the tracked map is kept within
        ``max_entries``.

        :param totp: the :class:`pyotp.TOTP` used to check ``otp``.
        :param otp: the one-time code presented by the client.
        :param account_id: identifies whose code this is; codes are tracked per
            account so two accounts never collide.
        :param for_time: the time to verify at; defaults to now. Use the time
            step this ``for_time`` falls in when tracking the consumed code.
        :returns: ``True`` if the code is valid and has not been used before,
            ``False`` if it is invalid or has already been consumed.
        """
        if for_time is None:
            for_time = datetime.datetime.now()

        time_step = totp.timecode(for_time)

        # Reclaim only records whose time step has fully elapsed. Such a code can
        # never verify again (its step is in the past), so forgetting it cannot
        # readmit a replay. This keeps memory bounded under churn without ever
        # discarding a record whose window is still open.
        for existing_key in list(self._consumed):
            if existing_key[1] < time_step:
                del self._consumed[existing_key]

        if not totp.verify(otp, for_time=for_time):
            return False

        key = (account_id, time_step)
        if key in self._consumed:
            # Already accepted this code in this window: a replay.
            return False

        if len(self._consumed) >= self.max_entries:
            # The bound is reached and nothing expired can be reclaimed. Every
            # tracked record is still inside its window, so evicting one would
            # forget a live consumed code and let it replay. Fail closed for the
            # new request instead; the bound holds and no code is readmitted.
            return False

        self._consumed[key] = {"account_id": account_id, "time_step": time_step}
        return True
