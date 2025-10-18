# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["CounterPricingListParams"]


class CounterPricingListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    date: str
    """Date on which to retrieve active CounterPricings."""

    ids: SequenceNotStr[str]
    """List of CounterPricing IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of CounterPricings to retrieve per page."""

    plan_id: Annotated[str, PropertyInfo(alias="planId")]
    """UUID of the Plan to retrieve CounterPricings for."""

    plan_template_id: Annotated[str, PropertyInfo(alias="planTemplateId")]
    """UUID of the Plan Template to retrieve CounterPricings for."""
