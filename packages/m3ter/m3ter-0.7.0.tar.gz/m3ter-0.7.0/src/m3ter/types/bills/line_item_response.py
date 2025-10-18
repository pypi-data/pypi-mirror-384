# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["LineItemResponse", "BandUsage"]


class BandUsage(BaseModel):
    band_quantity: Optional[float] = FieldInfo(alias="bandQuantity", default=None)
    """Usage amount within the band."""

    band_subtotal: Optional[float] = FieldInfo(alias="bandSubtotal", default=None)
    """Subtotal amount for the band."""

    band_units: Optional[float] = FieldInfo(alias="bandUnits", default=None)
    """The number of units used within the band."""

    converted_band_subtotal: Optional[float] = FieldInfo(alias="convertedBandSubtotal", default=None)

    credit_type_id: Optional[str] = FieldInfo(alias="creditTypeId", default=None)
    """The UUID of the credit type."""

    fixed_price: Optional[float] = FieldInfo(alias="fixedPrice", default=None)
    """
    Fixed price is a charge entered for certain pricing types such as Stairstep,
    Custom Tiered, and Custom Volume. It is a set price and not dependent on usage.
    """

    lower_limit: Optional[float] = FieldInfo(alias="lowerLimit", default=None)
    """The lower limit _(start)_ of the pricing band."""

    pricing_band_id: Optional[str] = FieldInfo(alias="pricingBandId", default=None)
    """The UUID for the pricing band."""

    unit_price: Optional[float] = FieldInfo(alias="unitPrice", default=None)
    """The price per unit in the band."""

    unit_subtotal: Optional[float] = FieldInfo(alias="unitSubtotal", default=None)
    """The subtotal of the unit usage."""


class LineItemResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accounting_product_code: Optional[str] = FieldInfo(alias="accountingProductCode", default=None)
    """The code of the Accounting Product associated with this line item."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)
    """The unique identifier (UUID) for the associated Accounting Product."""

    accounting_product_name: Optional[str] = FieldInfo(alias="accountingProductName", default=None)
    """The name of the Accounting Product associated with this line item."""

    additional: Optional[Dict[str, object]] = None

    aggregation_id: Optional[str] = FieldInfo(alias="aggregationId", default=None)
    """
    A unique identifier (UUID) for the Aggregation that contributes to this Bill
    line item.
    """

    average_unit_price: Optional[float] = FieldInfo(alias="averageUnitPrice", default=None)
    """
    Represents the average unit price calculated across all pricing bands or tiers
    for this line item.
    """

    balance_id: Optional[str] = FieldInfo(alias="balanceId", default=None)

    band_usage: Optional[List[BandUsage]] = FieldInfo(alias="bandUsage", default=None)
    """
    Array containing the pricing band information, which shows the details for each
    pricing band or tier.
    """

    bill_id: Optional[str] = FieldInfo(alias="billId", default=None)
    """The unique identifier (UUID) for the Bill that includes this line item."""

    charge_id: Optional[str] = FieldInfo(alias="chargeId", default=None)

    commitment_id: Optional[str] = FieldInfo(alias="commitmentId", default=None)
    """The unique identifier (UUID) of the Commitment _(if this is used)_."""

    compound_aggregation_id: Optional[str] = FieldInfo(alias="compoundAggregationId", default=None)
    """A unique identifier (UUID) for the Compound Aggregation, if applicable."""

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)
    """The unique identifier (UUID) for the contract associated with this line item."""

    conversion_rate: Optional[float] = FieldInfo(alias="conversionRate", default=None)
    """The currency conversion rate _(if used)_ for the line item."""

    converted_subtotal: Optional[float] = FieldInfo(alias="convertedSubtotal", default=None)
    """
    The subtotal amount for this line item after currency conversion, if applicable.
    """

    counter_id: Optional[str] = FieldInfo(alias="counterId", default=None)

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the Bill line item."""

    credit_type_id: Optional[str] = FieldInfo(alias="creditTypeId", default=None)
    """The unique identifier (UUID) for the type of credit applied to this line item."""

    currency: Optional[str] = None
    """The currency in which the line item is billed, represented as a currency code.

    For example, USD, GBP, or EUR.
    """

    description: Optional[str] = None
    """A detailed description providing context for the line item within the Bill."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time _(in ISO 8601 format)_ when the Bill line item was first
    created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO 8601 format)_ when the Bill line item was last
    modified.
    """

    group: Optional[Dict[str, str]] = None

    json_usage_generated: Optional[bool] = FieldInfo(alias="jsonUsageGenerated", default=None)
    """
    Boolean flag indicating whether the Bill line item has associated statement
    usage in JSON format. When a Bill statement is generated, usage line items have
    their usage stored in JSON format.

    See
    [Working with Bill Statements](https://www.m3ter.com/docs/guides/running-viewing-and-managing-bills/working-with-bill-statements)
    for more information.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) for the user who last modified this Bill line item.
    """

    line_item_type: Optional[
        Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ]
    ] = FieldInfo(alias="lineItemType", default=None)

    meter_id: Optional[str] = FieldInfo(alias="meterId", default=None)
    """The unique identifier (UUID) of the Meter responsible for tracking usage."""

    plan_group_id: Optional[str] = FieldInfo(alias="planGroupId", default=None)
    """The UUID of the PlanGroup.

    The unique identifier (UUID) for the PlanGroup, if applicable.
    """

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """A unique identifier (UUID) for the billing Plan associated with this line item,"""

    pricing_id: Optional[str] = FieldInfo(alias="pricingId", default=None)
    """The unique identifier (UUID) of the Pricing used for this line item,"""

    product_code: Optional[str] = FieldInfo(alias="productCode", default=None)
    """The code of the Product associated with this line item."""

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """The unique identifier (UUID) for the associated Product."""

    product_name: Optional[str] = FieldInfo(alias="productName", default=None)
    """The name of the Product associated with this line item."""

    quantity: Optional[float] = None
    """The amount of the product or service used in this line item."""

    reason_id: Optional[str] = FieldInfo(alias="reasonId", default=None)
    """The UUID of the reason used for the line item.

    A unique identifier (UUID) for the reason or justification for this line item,
    if applicable.
    """

    referenced_bill_id: Optional[str] = FieldInfo(alias="referencedBillId", default=None)
    """
    A unique identifier (UUID) for a Bill that this line item may be related to or
    derived from.
    """

    referenced_line_item_id: Optional[str] = FieldInfo(alias="referencedLineItemId", default=None)
    """
    A unique identifier (UUID) for another line item that this line item may be
    related to or derived from.
    """

    segment: Optional[Dict[str, str]] = None
    """Specifies the segment name or identifier when segmented Aggregation is used.

    This is relevant for more complex billing structures.
    """

    sequence_number: Optional[int] = FieldInfo(alias="sequenceNumber", default=None)
    """The number used for sequential invoices."""

    service_period_end_date: Optional[datetime] = FieldInfo(alias="servicePeriodEndDate", default=None)
    """The _(exclusive)_ end date for the service period in ISO 68601 format."""

    service_period_start_date: Optional[datetime] = FieldInfo(alias="servicePeriodStartDate", default=None)
    """The _(inclusive)_ start date for the service period in ISO 8601 format."""

    subtotal: Optional[float] = None
    """
    The subtotal amount when not currency converted _(in the cases where currency
    conversion is required)_.
    """

    unit: Optional[str] = None
    """Specifies the unit type. For example: **MB**, **GB**, **api_calls**, and so on."""

    units: Optional[float] = None
    """
    The number of units rated in the line item, each of which is of the type
    specified in the `unit` field. For example: 400 api_calls.

    In this example, the unit type of **api_calls** is read from the `unit` field.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
