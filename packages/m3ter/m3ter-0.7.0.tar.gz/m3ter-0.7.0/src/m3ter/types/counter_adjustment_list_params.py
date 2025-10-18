# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CounterAdjustmentListParams"]


class CounterAdjustmentListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """List CounterAdjustment items for the Account UUID."""

    counter_id: Annotated[str, PropertyInfo(alias="counterId")]
    """List CounterAdjustment items for the Counter UUID."""

    date: str
    """List CounterAdjustment items for the given date."""

    date_end: Annotated[Optional[str], PropertyInfo(alias="dateEnd")]

    date_start: Annotated[Optional[str], PropertyInfo(alias="dateStart")]

    end_date_end: Annotated[str, PropertyInfo(alias="endDateEnd")]
    """Only include CounterAdjustments with end dates earlier than this date."""

    end_date_start: Annotated[str, PropertyInfo(alias="endDateStart")]
    """
    Only include CounterAdjustments with end dates equal to or later than this date.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of CounterAdjustments to retrieve per page"""

    sort_order: Annotated[str, PropertyInfo(alias="sortOrder")]
    """Sort order for the results"""
