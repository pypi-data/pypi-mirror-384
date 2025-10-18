# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .shared_params.pricing_band import PricingBand

__all__ = ["PricingUpdateParams"]


class PricingUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

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

    aggregation_id: Annotated[str, PropertyInfo(alias="aggregationId")]
    """UUID of the Aggregation used to create the Pricing.

    Use this when creating a Pricing for a segmented aggregation.
    """

    code: str
    """Unique short code for the Pricing."""

    compound_aggregation_id: Annotated[str, PropertyInfo(alias="compoundAggregationId")]
    """UUID of the Compound Aggregation used to create the Pricing."""

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

    minimum_spend: Annotated[float, PropertyInfo(alias="minimumSpend")]
    """
    The minimum spend amount per billing cycle for end customer Accounts on a Plan
    to which the Pricing is applied.
    """

    minimum_spend_bill_in_advance: Annotated[bool, PropertyInfo(alias="minimumSpendBillInAdvance")]
    """The default value is **FALSE**.

    - When TRUE, minimum spend is billed at the start of each billing period.

    - When FALSE, minimum spend is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at Organization level for minimum spend
    billing in arrears/in advance.
    """

    minimum_spend_description: Annotated[str, PropertyInfo(alias="minimumSpendDescription")]
    """Minimum spend description _(displayed on the bill line item)_."""

    overage_pricing_bands: Annotated[Iterable[PricingBand], PropertyInfo(alias="overagePricingBands")]
    """
    Specify Prepayment/Balance overage pricing in pricing bands for the case of a
    **Tiered** pricing structure.
    """

    plan_id: Annotated[str, PropertyInfo(alias="planId")]
    """UUID of the Plan the Pricing is created for."""

    plan_template_id: Annotated[str, PropertyInfo(alias="planTemplateId")]
    """UUID of the Plan Template the Pricing is created for."""

    segment: Dict[str, str]
    """
    Specifies the segment value which you are defining a Pricing for using this
    call:

    - For each segment value defined on a Segmented Aggregation you must create a
      separate Pricing and use the appropriate `aggregationId` parameter for the
      call.
    - If you specify a segment value that has not been defined for the Aggregation,
      you'll receive an error.
    - If you've defined segment values for the Aggregation using a single wildcard
      or multiple wildcards, you can create Pricing for these wildcard segment
      values also.

    For more details on creating Pricings for segment values on a Segmented
    Aggregation using this call, together with some examples, see the
    [Using API Call to Create Segmented Pricings](https://www.m3ter.com/docs/guides/plans-and-pricing/pricing-plans/pricing-plans-using-segmented-aggregations#using-api-call-to-create-a-segmented-pricing)
    in our User Documentation.
    """

    tiers_span_plan: Annotated[bool, PropertyInfo(alias="tiersSpanPlan")]
    """The default value is **FALSE**.

    - If TRUE, usage accumulates over the entire period the priced Plan is active
      for the account, and is not reset for pricing band rates at the start of each
      billing period.

    - If FALSE, usage does not accumulate, and is reset for pricing bands at the
      start of each billing period.
    """

    type: Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"]
    """- **DEBIT**.

    Default setting. The amount calculated using the Pricing is added to the bill as
    a debit.

    - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
      bill as a credit _(negative amount)_. To prevent negative billing, the bill
      will be capped at the total of other line items for the same Product.

    - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
      bill as a credit _(negative amount)_. To prevent negative billing, the bill
      will be capped at the total of other line items for the entire bill, which
      might include other Products the Account consumes.
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
