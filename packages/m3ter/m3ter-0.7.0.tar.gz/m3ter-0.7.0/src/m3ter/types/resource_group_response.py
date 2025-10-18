# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ResourceGroupResponse"]


class ResourceGroupResponse(BaseModel):
    id: Optional[str] = None
    """The unique identifier (UUID) of the Resource Group."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Resource Group."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the Resource Group was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the Resource Group was last
    modified.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this Resource Group."""

    name: Optional[str] = None
    """The name of the Resource Group."""

    version: Optional[int] = None
    """The version number. Default value when newly created is one."""
