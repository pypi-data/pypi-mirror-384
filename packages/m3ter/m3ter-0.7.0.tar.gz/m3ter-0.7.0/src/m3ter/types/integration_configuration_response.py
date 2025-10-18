# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["IntegrationConfigurationResponse"]


class IntegrationConfigurationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    destination: str
    """The destination system for the integration run."""

    entity_id: str = FieldInfo(alias="entityId")
    """The unique identifier (UUID) of the entity the integration run is for."""

    entity_type: str = FieldInfo(alias="entityType")
    """The type of entity the integration run is for. Two options:

    - Bill
    - Notification
    """

    status: Literal[
        "WAITING",
        "STARTED",
        "COMPLETE",
        "ERROR",
        "AWAITING_RETRY",
        "AUTH_FAILED",
        "ACCOUNTING_PERIOD_CLOSED",
        "INVOICE_ALREADY_PAID",
        "DISABLED",
        "TIMEOUT_LIMIT_EXCEEDED",
        "RATE_LIMIT_RETRY",
    ]

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    dt_completed: Optional[datetime] = FieldInfo(alias="dtCompleted", default=None)
    """The date and time the integration was completed. _(in ISO-8601 format)_."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    dt_started: Optional[datetime] = FieldInfo(alias="dtStarted", default=None)
    """The date and time the integration run was started _(in ISO-8601 format)_."""

    error: Optional[str] = None
    """Describes any errors encountered during the integration run."""

    external_id: Optional[str] = FieldInfo(alias="externalId", default=None)
    """The external ID in the destination system if available."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    url: Optional[str] = None
    """The URL of the entity in the destination system if available."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
