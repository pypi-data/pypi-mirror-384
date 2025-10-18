# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["M3terSignedCredentialsRequestParam"]


class M3terSignedCredentialsRequestParam(TypedDict, total=False):
    api_key: Required[Annotated[str, PropertyInfo(alias="apiKey")]]
    """The API key provided by m3ter.

    This key is part of the credential set required for signing requests and
    authenticating with m3ter services.
    """

    secret: Required[str]
    """The secret associated with the API key.

    This secret is used in conjunction with the API key to generate a signature for
    secure authentication.
    """

    type: Required[Literal["M3TER_SIGNED_REQUEST"]]
    """Specifies the authorization type.

    For this schema, it is exclusively set to M3TER_SIGNED_REQUEST.
    """

    empty: bool
    """A flag to indicate whether the credentials are empty.

    - TRUE - empty credentials.
    - FALSE - credential details required.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
