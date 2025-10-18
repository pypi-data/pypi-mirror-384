# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["CompoundAggregationListParams"]


class CompoundAggregationListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    codes: SequenceNotStr[str]
    """
    An optional parameter to retrieve specific CompoundAggregations based on their
    short codes.
    """

    ids: SequenceNotStr[str]
    """
    An optional parameter to retrieve specific CompoundAggregations based on their
    unique identifiers (UUIDs).
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of CompoundAggregations in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of CompoundAggregations to retrieve per page."""

    product_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="productId")]
    """
    An optional parameter to filter the CompoundAggregations based on specific
    Product unique identifiers (UUIDs).
    """
