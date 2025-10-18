# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PlanGroupLinkResponse"]


class PlanGroupLinkResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this plan group link."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime _(in ISO-8601 format)_ when the plan group link was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime _(in ISO-8601 format)_ when the plan group link was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this plan group link."""

    plan_group_id: Optional[str] = FieldInfo(alias="planGroupId", default=None)
    """ID of the linked PlanGroup"""

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """ID of the linked Plan"""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
