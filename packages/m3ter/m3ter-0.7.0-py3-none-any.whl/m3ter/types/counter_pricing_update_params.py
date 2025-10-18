# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .shared_params.pricing_band import PricingBand

__all__ = ["CounterPricingUpdateParams"]


class CounterPricingUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    counter_id: Required[Annotated[str, PropertyInfo(alias="counterId")]]
    """UUID of the Counter used to create the pricing."""

    pricing_bands: Required[Annotated[Iterable[PricingBand], PropertyInfo(alias="pricingBands")]]

    start_date: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]]
    """
    The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
    for the Plan of Plan Template._(Required)_
    """

    accounting_product_id: Annotated[str, PropertyInfo(alias="accountingProductId")]
    """
    Optional Product ID this Pricing should be attributed to for accounting purposes
    """

    code: str
    """Unique short code for the Pricing."""

    cumulative: bool
    """
    Controls whether or not charge rates under a set of pricing bands configured for
    a Pricing are applied according to each separate band or at the highest band
    reached.

    _(Optional)_. The default value is **FALSE**.

    - When TRUE, at billing charge rates are applied according to each separate
      band.

    - When FALSE, at billing charge rates are applied according to highest band
      reached.

    **NOTE:** Use the `cumulative` parameter to create the type of Pricing you
    require. For example, for Tiered Pricing set to **TRUE**; for Volume Pricing,
    set to **FALSE**.
    """

    description: str
    """Displayed on Bill line items."""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """
    The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
    the Plan or Plan Template.

    _(Optional)_ If not specified, the Pricing remains active indefinitely.
    """

    plan_id: Annotated[str, PropertyInfo(alias="planId")]
    """UUID of the Plan the Pricing is created for."""

    plan_template_id: Annotated[str, PropertyInfo(alias="planTemplateId")]
    """UUID of the Plan Template the Pricing is created for."""

    pro_rate_adjustment_credit: Annotated[bool, PropertyInfo(alias="proRateAdjustmentCredit")]
    """The default value is **TRUE**.

    - When TRUE, counter adjustment credits are prorated and are billed according to
      the number of days in billing period.

    - When FALSE, counter adjustment credits are not prorated and are billed for the
      entire billing period.

    _(Optional)_.
    """

    pro_rate_adjustment_debit: Annotated[bool, PropertyInfo(alias="proRateAdjustmentDebit")]
    """The default value is **TRUE**.

    - When TRUE, counter adjustment debits are prorated and are billed according to
      the number of days in billing period.

    - When FALSE, counter adjustment debits are not prorated and are billed for the
      entire billing period.

    _(Optional)_.
    """

    pro_rate_running_total: Annotated[bool, PropertyInfo(alias="proRateRunningTotal")]
    """The default value is **TRUE**.

    - When TRUE, counter running total charges are prorated and are billed according
      to the number of days in billing period.

    - When FALSE, counter running total charges are not prorated and are billed for
      the entire billing period.

    _(Optional)_.
    """

    running_total_bill_in_advance: Annotated[bool, PropertyInfo(alias="runningTotalBillInAdvance")]
    """The default value is **TRUE**.

    - When TRUE, running totals are billed at the start of each billing period.

    - When FALSE, running totals are billed at the end of each billing period.

    _(Optional)_.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
