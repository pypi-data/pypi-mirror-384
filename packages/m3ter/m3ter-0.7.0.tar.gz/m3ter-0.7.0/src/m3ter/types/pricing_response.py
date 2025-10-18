# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.pricing_band import PricingBand

__all__ = ["PricingResponse"]


class PricingResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)

    aggregation_id: Optional[str] = FieldInfo(alias="aggregationId", default=None)
    """UUID of the Aggregation used to create the Pricing.

    Use this when creating a Pricing for a segmented aggregation.
    """

    aggregation_type: Optional[Literal["SIMPLE", "COMPOUND"]] = FieldInfo(alias="aggregationType", default=None)

    code: Optional[str] = None
    """Unique short code for the Pricing."""

    compound_aggregation_id: Optional[str] = FieldInfo(alias="compoundAggregationId", default=None)
    """UUID of the Compound Aggregation used to create the Pricing."""

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

    minimum_spend: Optional[float] = FieldInfo(alias="minimumSpend", default=None)
    """
    The minimum spend amount per billing cycle for end customer Accounts on a Plan
    to which the Pricing is applied.
    """

    minimum_spend_bill_in_advance: Optional[bool] = FieldInfo(alias="minimumSpendBillInAdvance", default=None)
    """The default value is **FALSE**.

    - When TRUE, minimum spend is billed at the start of each billing period.

    - When FALSE, minimum spend is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at Organization level for minimum spend
    billing in arrears/in advance.
    """

    minimum_spend_description: Optional[str] = FieldInfo(alias="minimumSpendDescription", default=None)
    """Minimum spend description _(displayed on the bill line item)_."""

    overage_pricing_bands: Optional[List[PricingBand]] = FieldInfo(alias="overagePricingBands", default=None)
    """
    The Prepayment/Balance overage pricing in pricing bands for the case of a
    **Tiered** pricing structure.
    """

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """UUID of the Plan the Pricing is created for."""

    plan_template_id: Optional[str] = FieldInfo(alias="planTemplateId", default=None)
    """UUID of the Plan Template the Pricing was created for."""

    pricing_bands: Optional[List[PricingBand]] = FieldInfo(alias="pricingBands", default=None)

    segment: Optional[Dict[str, str]] = None
    """Name of the segment for which you are defining a Pricing.

    For each segment in a segmented aggregation, make a separate call using
    `aggregationId` parameter to update a Pricing.
    """

    segment_string: Optional[str] = FieldInfo(alias="segmentString", default=None)

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """
    The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
    for the Plan of Plan Template.
    """

    tiers_span_plan: Optional[bool] = FieldInfo(alias="tiersSpanPlan", default=None)
    """The default value is **FALSE**.

    - If TRUE, usage accumulates over the entire period the priced Plan is active
      for the account, and is not reset for pricing band rates at the start of each
      billing period.

    - If FALSE, usage does not accumulate, and is reset for pricing bands at the
      start of each billing period.
    """

    type: Optional[Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"]] = None
    """- **DEBIT**.

    Default setting. The amount calculated using the Pricing is added to the bill as
    a debit.

    - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
      bill as a credit _(negative amount)_. To prevent negative billing, the bill
      will be capped at the total of other line items for the _same_ Product.

    - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
      bill as a credit _(negative amount)_. To prevent negative billing, the bill
      will be capped at the total of other line items for the entire bill, which
      might include other Products the Account consumes.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
