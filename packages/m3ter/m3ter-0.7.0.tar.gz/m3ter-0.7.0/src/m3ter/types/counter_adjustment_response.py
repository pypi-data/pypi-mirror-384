# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CounterAdjustmentResponse"]


class CounterAdjustmentResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """The Account ID the CounterAdjustment was created for."""

    counter_id: Optional[str] = FieldInfo(alias="counterId", default=None)
    """
    The ID of the Counter that was used to make the CounterAdjustment on the
    Account.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    date: Optional[datetime.date] = None
    """
    The date the CounterAdjustment was created for the Account _(in ISO-8601 date
    format)_.
    """

    dt_created: Optional[datetime.datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime.datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)
    """Purchase Order Number for the Counter Adjustment. _(Optional)_"""

    value: Optional[int] = None
    """Integer Value of the Counter that was used to make the CounterAdjustment."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
