# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import date, datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["BillConfigResponse"]


class BillConfigResponse(BaseModel):
    id: Optional[str] = None
    """The Organization UUID.

    The Organization represents your company as a direct customer of the m3ter
    service.
    """

    bill_lock_date: Optional[date] = FieldInfo(alias="billLockDate", default=None)
    """The global lock date _(in ISO 8601 format)_ when all Bills will be locked.

    For example: `"2024-03-01"`.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this bill config."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime _(in ISO-8601 format)_ when the bill config was first created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime _(in ISO-8601 format)_ when the bill config was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this bill config."""

    version: Optional[int] = None
    """The version number:

    - Default value when newly created is one.
    - Incremented by 1 each time it is updated.
    """
