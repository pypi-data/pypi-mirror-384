# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["AccountPlanListParams"]


class AccountPlanListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account: str
    """
    The unique identifier (UUID) for the Account whose AccountPlans and
    AccountPlanGroups you want to retrieve.

    **NOTE:** Only returns the currently active AccountPlans and AccountPlanGroups
    for the specified Account. Use in combination with the `includeall` query
    parameter to return both active and inactive.
    """

    contract: Optional[str]
    """
    The unique identifier (UUID) of the Contract which the AccountPlans you want to
    retrieve have been linked to.

    **NOTE:** Does not return AccountPlanGroups that have been linked to the
    Contract.
    """

    date: str
    """
    The specific date for which you want to retrieve AccountPlans and
    AccountPlanGroups.

    **NOTE:** Returns both active and inactive AccountPlans and AccountPlanGroups
    for the specified date.
    """

    ids: SequenceNotStr[str]
    """
    A list of unique identifiers (UUIDs) for specific AccountPlans and
    AccountPlanGroups you want to retrieve.
    """

    includeall: bool
    """
    A Boolean flag that specifies whether to include both active and inactive
    AccountPlans and AccountPlanGroups in the list.

    - **TRUE** - both active and inactive AccountPlans and AccountPlanGroups are
      included in the list.
    - **FALSE** - only active AccountPlans and AccountPlanGroups are retrieved in
      the list.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """
    The `nextToken` for retrieving the next page of AccountPlans and
    AccountPlanGroups. It is used to fetch the next page of AccountPlans and
    AccountPlanGroups in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """The maximum number of AccountPlans and AccountPlanGroups to return per page."""

    plan: str
    """
    The unique identifier (UUID) for the Plan whose associated AccountPlans you want
    to retrieve.

    **NOTE:** Does not return AccountPlanGroups if you use a `planGroupId`.
    """

    product: str
    """
    The unique identifier (UUID) for the Product whose associated AccountPlans you
    want to retrieve.

    **NOTE:** You cannot use the `product` query parameter as a single filter
    condition, but must always use it in combination with the `account` query
    parameter.
    """
