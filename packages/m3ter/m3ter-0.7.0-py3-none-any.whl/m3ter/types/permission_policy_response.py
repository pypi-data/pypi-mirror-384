# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .permission_statement_response import PermissionStatementResponse

__all__ = ["PermissionPolicyResponse"]


class PermissionPolicyResponse(BaseModel):
    id: Optional[str] = None
    """The unique identifier (UUID) for this Permission Policy."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Permission Policy."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the Permission Policy was created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the Permission Policy was last
    modified.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) of the user who last modified this Permission
    Policy.
    """

    managed_policy: Optional[bool] = FieldInfo(alias="managedPolicy", default=None)
    """Indicates whether this is a system generated Managed Permission Policy."""

    name: Optional[str] = None
    """The name of the Permission Policy."""

    permission_policy: Optional[List[PermissionStatementResponse]] = FieldInfo(alias="permissionPolicy", default=None)
    """Array containing the Permission Policies information."""

    version: Optional[int] = None
    """The version number. Default value when newly created is one."""
