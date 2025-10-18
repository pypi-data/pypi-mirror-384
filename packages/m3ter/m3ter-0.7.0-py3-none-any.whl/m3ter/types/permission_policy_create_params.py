# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .permission_statement_response_param import PermissionStatementResponseParam

__all__ = ["PermissionPolicyCreateParams"]


class PermissionPolicyCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    name: Required[str]

    permission_policy: Required[
        Annotated[Iterable[PermissionStatementResponseParam], PropertyInfo(alias="permissionPolicy")]
    ]

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - do not use
      for Create. On initial Create, version is set at 1 and listed in the response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
