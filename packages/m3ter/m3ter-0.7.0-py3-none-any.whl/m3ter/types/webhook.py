# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .m3ter_signed_credentials_response import M3terSignedCredentialsResponse

__all__ = ["Webhook"]


class Webhook(BaseModel):
    id: str
    """The UUID of the entity."""

    active: Optional[bool] = None

    code: Optional[str] = None

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    credentials: Optional[M3terSignedCredentialsResponse] = None
    """Response representing a set of credentials used for signing m3ter requests."""

    description: Optional[str] = None

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    name: Optional[str] = None

    url: Optional[str] = None
    """The URL to which webhook requests are sent."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
