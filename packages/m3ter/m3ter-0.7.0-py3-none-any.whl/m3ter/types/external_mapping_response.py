# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ExternalMappingResponse"]


class ExternalMappingResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    external_id: str = FieldInfo(alias="externalId")
    """The unique identifier (UUID) of the entity in the external system."""

    external_system: str = FieldInfo(alias="externalSystem")
    """The name of the external system where the entity you are mapping resides."""

    external_table: str = FieldInfo(alias="externalTable")
    """The name of the table in the external system where the entity resides."""

    m3ter_entity: str = FieldInfo(alias="m3terEntity")
    """The name of the m3ter entity that is part of the External Mapping.

    For example, this could be "Account".
    """

    m3ter_id: str = FieldInfo(alias="m3terId")
    """The unique identifier (UUID) of the m3ter entity."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    integration_config_id: Optional[str] = FieldInfo(alias="integrationConfigId", default=None)
    """UUID of the configuration this mapping is for"""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
