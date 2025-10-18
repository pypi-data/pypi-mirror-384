# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CreditLineItemResponse"]


class CreditLineItemResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    amount: float
    """The amount for the line item."""

    description: str
    """The description of the line item."""

    product_id: str = FieldInfo(alias="productId")
    """The UUID of the Product."""

    referenced_bill_id: str = FieldInfo(alias="referencedBillId")
    """The UUID of the bill for the line item."""

    referenced_line_item_id: str = FieldInfo(alias="referencedLineItemId")
    """The UUID of the line item."""

    service_period_end_date: datetime = FieldInfo(alias="servicePeriodEndDate")
    """The service period end date in ISO-8601 format.

    _(exclusive of the ending date)_.
    """

    service_period_start_date: datetime = FieldInfo(alias="servicePeriodStartDate")
    """The service period start date in ISO-8601 format.

    _(inclusive of the starting date)_.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this credit line item."""

    credit_reason_id: Optional[str] = FieldInfo(alias="creditReasonId", default=None)
    """The UUID of the credit reason for this credit line item."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the credit line item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The DateTime when the credit line item was last modified _(in ISO-8601 format)_.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this credit line item."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
