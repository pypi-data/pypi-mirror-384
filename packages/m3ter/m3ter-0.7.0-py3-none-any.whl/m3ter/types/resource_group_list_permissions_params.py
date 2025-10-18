# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ResourceGroupListPermissionsParams"]


class ResourceGroupListPermissionsParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    type: Required[str]

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of PermissionPolicy entities to retrieve per page"""
