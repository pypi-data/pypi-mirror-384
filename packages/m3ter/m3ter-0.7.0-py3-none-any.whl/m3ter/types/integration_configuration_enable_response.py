# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["IntegrationConfigurationEnableResponse"]


class IntegrationConfigurationEnableResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    destination: str
    """The type of destination _(e.g. Netsuite, webhooks)_."""

    entity_type: str = FieldInfo(alias="entityType")
    """The type of entity the integration is for _(e.g. Bill)_."""

    authorized: Optional[bool] = None
    """A flag indicating whether the integration configuration is authorized.

    - TRUE - authorized.
    - FALSE - not authorized.
    """

    config_data: Optional[Dict[str, object]] = FieldInfo(alias="configData", default=None)
    """Configuration data for the integration"""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    destination_id: Optional[str] = FieldInfo(alias="destinationId", default=None)
    """The unique identifier (UUID) of the entity the integration is for."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    enabled: Optional[bool] = None
    """
    A flag indicating whether the integration configuration is currently enabled or
    disabled.

    - TRUE - enabled.
    - FALSE - disabled.
    """

    entity_id: Optional[str] = FieldInfo(alias="entityId", default=None)
    """The unique identifier (UUID) of the entity this integration is for \\**(e.g.

    the ID of a notification configuration. Optional.)\\**
    """

    integration_credentials_id: Optional[str] = FieldInfo(alias="integrationCredentialsId", default=None)
    """UUID of the credentials to use for this integration"""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    name: Optional[str] = None
    """The name of the configuration"""

    trigger_type: Optional[Literal["EVENT", "SCHEDULE"]] = FieldInfo(alias="triggerType", default=None)
    """Specifies the type of trigger for the integration."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
