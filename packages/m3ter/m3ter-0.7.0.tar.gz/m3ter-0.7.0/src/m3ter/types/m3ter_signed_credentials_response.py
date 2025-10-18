# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["M3terSignedCredentialsResponse"]


class M3terSignedCredentialsResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    destination: str
    """the system the integration is for"""

    type: str
    """the type of credentials"""

    api_key: Optional[str] = FieldInfo(alias="apiKey", default=None)
    """The API key provided by m3ter.

    This key is part of the credential set required for signing requests and
    authenticating with m3ter services.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    destination_id: Optional[str] = FieldInfo(alias="destinationId", default=None)
    """the destinationId the integration is for"""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    name: Optional[str] = None
    """the name of the credentials"""

    secret: Optional[str] = None
    """The secret associated with the API key.

    This secret is used in conjunction with the API key to generate a signature for
    secure authentication.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
