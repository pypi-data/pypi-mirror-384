# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["BillListParams"]


class BillListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """Optional filter.

    An Account ID - returns the Bills for the single specified Account.
    """

    additional: SequenceNotStr[str]
    """Comma separated list of additional fields."""

    bill_date: Annotated[str, PropertyInfo(alias="billDate")]
    """The specific date in ISO 8601 format for which you want to retrieve Bills."""

    bill_date_end: Annotated[str, PropertyInfo(alias="billDateEnd")]
    """Only include Bills with bill dates earlier than this date."""

    bill_date_start: Annotated[str, PropertyInfo(alias="billDateStart")]
    """Only include Bills with bill dates equal to or later than this date."""

    billing_frequency: Annotated[Optional[str], PropertyInfo(alias="billingFrequency")]

    exclude_line_items: Annotated[bool, PropertyInfo(alias="excludeLineItems")]
    """Exclude Line Items"""

    external_invoice_date_end: Annotated[str, PropertyInfo(alias="externalInvoiceDateEnd")]
    """Only include Bills with external invoice dates earlier than this date."""

    external_invoice_date_start: Annotated[str, PropertyInfo(alias="externalInvoiceDateStart")]
    """
    Only include Bills with external invoice dates equal to or later than this date.
    """

    ids: SequenceNotStr[str]
    """Optional filter. The list of Bill IDs to retrieve."""

    include_bill_total: Annotated[bool, PropertyInfo(alias="includeBillTotal")]
    """Include Bill Total"""

    locked: bool
    """Boolean flag specifying whether to include Bills with "locked" status.

    - **TRUE** - the list inlcudes "locked" Bills.
    - **FALSE** - excludes "locked" Bills from the list.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Bills in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of Bills to retrieve per page."""

    status: Literal["PENDING", "APPROVED"]
    """Only include Bills having the given status"""
