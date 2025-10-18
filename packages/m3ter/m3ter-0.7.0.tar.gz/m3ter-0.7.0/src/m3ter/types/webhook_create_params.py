# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .m3ter_signed_credentials_request_param import M3terSignedCredentialsRequestParam

__all__ = ["WebhookCreateParams"]


class WebhookCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    credentials: Required[M3terSignedCredentialsRequestParam]
    """This schema defines the credentials required for m3ter request signing."""

    description: Required[str]

    name: Required[str]

    url: Required[str]
    """The URL to which the webhook requests will be sent."""

    active: bool

    code: str

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
