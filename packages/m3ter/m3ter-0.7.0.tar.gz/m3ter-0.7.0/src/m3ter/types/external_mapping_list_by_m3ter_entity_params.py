# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExternalMappingListByM3terEntityParams"]


class ExternalMappingListByM3terEntityParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    entity: Required[str]

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of External Mappings in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of External Mappings to retrieve per page."""
