# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["PlanGroupListParams"]


class PlanGroupListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountId")]
    """Optional filter. The list of Account IDs to which the PlanGroups belong."""

    ids: SequenceNotStr[str]
    """Optional filter. The list of PlanGroup IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of PlanGroups in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of PlanGroups to retrieve per page."""
