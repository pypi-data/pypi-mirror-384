# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["CounterListParams"]


class CounterListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    codes: SequenceNotStr[str]
    """List of Counter codes to retrieve.

    These are unique short codes to identify each Counter.
    """

    ids: SequenceNotStr[str]
    """List of Counter IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """NextToken for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Counters to retrieve per page"""

    product_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="productId")]
    """List of Products UUIDs to retrieve Counters for."""
