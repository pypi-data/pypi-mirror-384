# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["AuthenticationGetBearerTokenResponse"]


class AuthenticationGetBearerTokenResponse(BaseModel):
    access_token: str
    """The access token."""

    expires_in: int
    """Token expiry time in seconds."""

    scope: Optional[str] = None
    """Not used."""

    token_type: Optional[str] = None
    """The token type, which in this case is "bearer"."""
