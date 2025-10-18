# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ResourceGroupListContentsResponse"]


class ResourceGroupListContentsResponse(BaseModel):
    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this item for the resource group."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the item was created for the resource group."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the resource group item was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this item for the resource group."""

    target_id: Optional[str] = FieldInfo(alias="targetId", default=None)
    """The UUID of the item."""

    target_type: Optional[Literal["ITEM", "GROUP"]] = FieldInfo(alias="targetType", default=None)
