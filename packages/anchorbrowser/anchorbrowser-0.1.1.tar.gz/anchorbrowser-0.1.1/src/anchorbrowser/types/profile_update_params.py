# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["ProfileUpdateParams"]


class ProfileUpdateParams(TypedDict, total=False):
    description: str
    """The new description for the profile."""

    session_id: str
    """The browser session ID is required if the source is set to `session`.

    The browser session must belong to the user and be active.
    """

    source: Literal["session"]
    """The source of the profile data. Currently, only `session` is supported."""
