# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["BillApproveParams"]


class BillApproveParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_ids: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="billIds")]]
    """Use to specify a collection of Bills by their IDs for batch approval"""

    account_ids: Annotated[str, PropertyInfo(alias="accountIds")]
    """List of Account IDs to filter Bills.

    This allows you to approve Bills for specific Accounts within the Organization.
    """

    external_invoice_date_end: Annotated[str, PropertyInfo(alias="externalInvoiceDateEnd")]
    """End date for filtering Bills by external invoice date.

    Includes Bills with dates earlier than this date.
    """

    external_invoice_date_start: Annotated[str, PropertyInfo(alias="externalInvoiceDateStart")]
    """Start date for filtering Bills by external invoice date.

    Includes Bills with dates equal to or later than this date.
    """
