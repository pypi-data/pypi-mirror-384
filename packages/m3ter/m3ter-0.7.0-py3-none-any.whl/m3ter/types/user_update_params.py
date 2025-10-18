# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo
from .permission_statement_response_param import PermissionStatementResponseParam

__all__ = ["UserUpdateParams"]


class UserUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    dt_end_access: Annotated[Union[str, datetime], PropertyInfo(alias="dtEndAccess", format="iso8601")]
    """The date and time _(in ISO 8601 format)_ when the user's access will end.

    Use this to set or update the expiration of the user's access.
    """

    permission_policy: Annotated[Iterable[PermissionStatementResponseParam], PropertyInfo(alias="permissionPolicy")]
    """An array of permission statements for the user.

    Each permission statement defines a specific permission for the user.

    See
    [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions)
    for more information.
    """

    version: int
    """The version number of the entity:

    - **Newly created entity:** On initial Create, version is set at 1 and listed in
      the response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
