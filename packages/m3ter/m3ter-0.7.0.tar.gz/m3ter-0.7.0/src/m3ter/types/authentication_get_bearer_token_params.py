# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["AuthenticationGetBearerTokenParams"]


class AuthenticationGetBearerTokenParams(TypedDict, total=False):
    grant_type: Required[Literal["client_credentials"]]
    """The grant type."""

    scope: str
    """Not used. The JWT scope."""
