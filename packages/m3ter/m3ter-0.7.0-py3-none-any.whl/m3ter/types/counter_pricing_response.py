# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.pricing_band import PricingBand

__all__ = ["CounterPricingResponse"]


class CounterPricingResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)

    code: Optional[str] = None
    """Unique short code for the Pricing."""

    counter_id: Optional[str] = FieldInfo(alias="counterId", default=None)
    """UUID of the Counter used to create the pricing."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The ID of the user who created this item."""

    cumulative: Optional[bool] = None
    """
    Controls whether or not charge rates under a set of pricing bands configured for
    a Pricing are applied according to each separate band or at the highest band
    reached.

    The default value is **TRUE**.

    - When TRUE, at billing charge rates are applied according to each separate
      band.

    - When FALSE, at billing charge rates are applied according to highest band
      reached.
    """

    description: Optional[str] = None
    """Displayed on Bill line items."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when this item was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when this item was last modified _(in ISO-8601 format)_."""

    end_date: Optional[datetime] = FieldInfo(alias="endDate", default=None)
    """
    The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
    the Plan or Plan Template.

    If not specified, the Pricing remains active indefinitely.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The ID of the user who last modified this item."""

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """UUID of the Plan the Pricing is created for."""

    plan_template_id: Optional[str] = FieldInfo(alias="planTemplateId", default=None)
    """UUID of the Plan Template the Pricing was created for."""

    pricing_bands: Optional[List[PricingBand]] = FieldInfo(alias="pricingBands", default=None)

    pro_rate_adjustment_credit: Optional[bool] = FieldInfo(alias="proRateAdjustmentCredit", default=None)
    """The default value is **TRUE**.

    - When TRUE, counter adjustment credits are prorated and are billed according to
      the number of days in billing period.

    - When FALSE, counter adjustment credits are not prorated and are billed for the
      entire billing period.
    """

    pro_rate_adjustment_debit: Optional[bool] = FieldInfo(alias="proRateAdjustmentDebit", default=None)
    """The default value is **TRUE**.

    - When TRUE, counter adjustment debits are prorated and are billed according to
      the number of days in billing period.

    - When FALSE, counter adjustment debits are not prorated and are billed for the
      entire billing period.
    """

    pro_rate_running_total: Optional[bool] = FieldInfo(alias="proRateRunningTotal", default=None)
    """The default value is **TRUE**.

    - When TRUE, counter running total charges are prorated and are billed according
      to the number of days in billing period.

    - When FALSE, counter running total charges are not prorated and are billed for
      the entire billing period.
    """

    running_total_bill_in_advance: Optional[bool] = FieldInfo(alias="runningTotalBillInAdvance", default=None)
    """The default value is **TRUE**.

    - When TRUE, running totals are billed at the start of each billing period.

    - When FALSE, running totals are billed at the end of each billing period.
    """

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """
    The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
    for the Plan of Plan Template.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
