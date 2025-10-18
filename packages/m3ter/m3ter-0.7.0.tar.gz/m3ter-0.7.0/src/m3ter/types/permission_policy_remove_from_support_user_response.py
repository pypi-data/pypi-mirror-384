# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PermissionPolicyRemoveFromSupportUserResponse"]


class PermissionPolicyRemoveFromSupportUserResponse(BaseModel):
    id: Optional[str] = None

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this principal permission."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime _(in ISO-8601 format)_ when the principal permission was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The DateTime _(in ISO-8601 format)_ when the principal permission was last
    modified.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this principal permission."""

    permission_policy_id: Optional[str] = FieldInfo(alias="permissionPolicyId", default=None)

    principal_id: Optional[str] = FieldInfo(alias="principalId", default=None)

    principal_type: Optional[Literal["USER", "USERGROUP", "SERVICEUSER", "SUPPORTUSERS"]] = FieldInfo(
        alias="principalType", default=None
    )

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
