"""The change feed store.

The dashboard shows account admins a chronological feed of "what changed" on
their team's account records -- plan upgrades, status flips, profile edits. Each
feed entry is a small dict that is appended to ``ChangeFeed`` and later rendered
in the web UI and included in the weekly summary email.
"""

from __future__ import annotations

from typing import Any


class ChangeFeed:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, entry: dict) -> None:
        """Append one rendered feed entry."""
        self._entries.append(entry)

    def entries(self) -> list[dict]:
        return list(self._entries)

    def __len__(self) -> int:
        return len(self._entries)
