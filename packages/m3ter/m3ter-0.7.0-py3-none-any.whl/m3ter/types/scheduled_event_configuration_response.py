# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ScheduledEventConfigurationResponse"]


class ScheduledEventConfigurationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    entity: str
    """
    The referenced configuration or billing entity for which the desired scheduled
    Event will trigger.
    """

    field: str
    """
    A DateTime field for which the desired scheduled Event will trigger - this must
    be a DateTime field on the referenced billing or configuration entity.
    """

    name: str
    """The name of the custom Scheduled Event Configuration."""

    offset: int
    """
    The offset in days from the specified DateTime field on the referenced entity
    when the scheduled Event will trigger.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
