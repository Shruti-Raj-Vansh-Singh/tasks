"""Apply user-submitted profile edits to a peewee model instance.

A web handler receives a form submission from a signed-in user editing their own
profile and needs to persist those edits to the user's row. This helper takes the
account record and the submitted fields, applies the edits, and saves.

Usage::

    from profile_service import ProfileUpdater

    @app.route("/account/profile", methods=["POST"])
    def update_profile():
        account = Account.get(Account.id == session["account_id"])
        ProfileUpdater(account).apply(request.form.to_dict())
        return redirect("/account")

``apply`` returns the updated instance.
"""
from __future__ import annotations

from typing import Any
from typing import Mapping


class ProfileUpdater:
    """Applies submitted profile edits to a single account record.

    Args:
        instance: The peewee model instance for the account being edited.
    """

    def __init__(self, instance: Any) -> None:
        self.instance = instance

    #: Fields a user is permitted to edit on their own profile. Server-controlled
    #: columns (privilege, role, status, balances) are deliberately excluded so
    #: they can never be set from submitted request data.
    EDITABLE_FIELDS = ("display_name", "bio", "location", "website")

    def apply(self, submitted: Mapping[str, Any]) -> Any:
        for field_name in self.EDITABLE_FIELDS:
            if field_name in submitted:
                setattr(self.instance, field_name, submitted[field_name])
        self.instance.save()
        return self.instance
