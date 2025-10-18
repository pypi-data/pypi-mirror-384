# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["PlanListParams"]


class PlanListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountId")]
    """List of Account IDs the Plan belongs to."""

    ids: SequenceNotStr[str]
    """List of Plan IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi-page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Plans to retrieve per page."""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """UUID of the Product to retrieve Plans for."""
