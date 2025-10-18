# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.currency_conversion import CurrencyConversion

__all__ = ["BillResponse", "LineItem", "LineItemUsagePerPricingBand"]


class LineItemUsagePerPricingBand(BaseModel):
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


class LineItem(BaseModel):
    average_unit_price: float = FieldInfo(alias="averageUnitPrice")
    """The average unit price across all tiers / pricing bands."""

    conversion_rate: float = FieldInfo(alias="conversionRate")
    """
    The currency conversion rate if currency conversion is required for the line
    item.
    """

    converted_subtotal: float = FieldInfo(alias="convertedSubtotal")
    """The converted subtotal amount if currency conversions have been used."""

    currency: str
    """The currency code for the currency used in the line item.

    For example: USD, GBP, or EUR.
    """

    description: str
    """Line item description."""

    line_item_type: Literal[
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
    ] = FieldInfo(alias="lineItemType")

    quantity: float
    """The amount of usage for the line item."""

    subtotal: float
    """The subtotal amount for the line item, before any currency conversions."""

    unit: str
    """The unit for the usage data in thie line item.

    For example: **GB** of disk storage space.
    """

    units: float
    """The number of units used for the line item."""

    id: Optional[str] = None
    """The UUID for the line item."""

    accounting_product_code: Optional[str] = FieldInfo(alias="accountingProductCode", default=None)

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)

    accounting_product_name: Optional[str] = FieldInfo(alias="accountingProductName", default=None)

    additional: Optional[Dict[str, object]] = None

    aggregation_id: Optional[str] = FieldInfo(alias="aggregationId", default=None)
    """The Aggregation ID used for the line item."""

    balance_id: Optional[str] = FieldInfo(alias="balanceId", default=None)

    charge_id: Optional[str] = FieldInfo(alias="chargeId", default=None)

    child_account_code: Optional[str] = FieldInfo(alias="childAccountCode", default=None)
    """
    If part of a Parent/Child account billing hierarchy, this is the code for the
    child Account.
    """

    child_account_id: Optional[str] = FieldInfo(alias="childAccountId", default=None)
    """
    If part of a Parent/Child account billing hierarchy, this is the child Account
    UUID.
    """

    commitment_id: Optional[str] = FieldInfo(alias="commitmentId", default=None)
    """
    If Commitments _(prepayments)_ are used in the line item, this shows the
    Commitment UUID.
    """

    compound_aggregation_id: Optional[str] = FieldInfo(alias="compoundAggregationId", default=None)
    """
    The Compound Aggregation ID for the line item if a Compound Aggregation has been
    used.
    """

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)
    """The UUID for the Contract used in the line item."""

    counter_id: Optional[str] = FieldInfo(alias="counterId", default=None)

    credit_type_id: Optional[str] = FieldInfo(alias="creditTypeId", default=None)

    group: Optional[Dict[str, str]] = None

    meter_id: Optional[str] = FieldInfo(alias="meterId", default=None)
    """The UUID of the Meter used in the line item."""

    plan_group_id: Optional[str] = FieldInfo(alias="planGroupId", default=None)
    """The UUID of the PlanGroup, provided the line item used a PlanGroup."""

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """The ID of the Plan used for the line item."""

    pricing_id: Optional[str] = FieldInfo(alias="pricingId", default=None)
    """The UUID of the Pricing used on the line item."""

    product_code: Optional[str] = FieldInfo(alias="productCode", default=None)

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """The UUID of the Product for the line item."""

    product_name: Optional[str] = FieldInfo(alias="productName", default=None)
    """The name of the Product for the line item."""

    reason_id: Optional[str] = FieldInfo(alias="reasonId", default=None)

    referenced_bill_id: Optional[str] = FieldInfo(alias="referencedBillId", default=None)

    referenced_line_item_id: Optional[str] = FieldInfo(alias="referencedLineItemId", default=None)

    segment: Optional[Dict[str, str]] = None
    """Applies only when segmented Aggregations have been used.

    The Segment to which the usage data in this line item belongs.
    """

    sequence_number: Optional[int] = FieldInfo(alias="sequenceNumber", default=None)
    """The number used for sequential invoices."""

    service_period_end_date: Optional[datetime] = FieldInfo(alias="servicePeriodEndDate", default=None)
    """The ending date _(exclusive)_ for the service period _(in ISO 8601 format)_."""

    service_period_start_date: Optional[datetime] = FieldInfo(alias="servicePeriodStartDate", default=None)
    """The starting date _(inclusive)_ for the service period _(in ISO 8601 format)_."""

    usage_per_pricing_band: Optional[List[LineItemUsagePerPricingBand]] = FieldInfo(
        alias="usagePerPricingBand", default=None
    )
    """Shows the usage by pricing band for tiered pricing structures."""


class BillResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_code: Optional[str] = FieldInfo(alias="accountCode", default=None)

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)

    approved_by: Optional[str] = FieldInfo(alias="approvedBy", default=None)
    """The id of the user who approved this bill."""

    bill_date: Optional[date] = FieldInfo(alias="billDate", default=None)

    bill_frequency_interval: Optional[int] = FieldInfo(alias="billFrequencyInterval", default=None)

    billing_frequency: Optional[Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"]] = FieldInfo(
        alias="billingFrequency", default=None
    )

    bill_job_id: Optional[str] = FieldInfo(alias="billJobId", default=None)

    bill_total: Optional[float] = FieldInfo(alias="billTotal", default=None)
    """The sum total for the Bill."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the Bill."""

    created_date: Optional[datetime] = FieldInfo(alias="createdDate", default=None)

    csv_statement_generated: Optional[bool] = FieldInfo(alias="csvStatementGenerated", default=None)
    """
    Flag to indicate that the statement in CSV format has been generated for the
    Bill.

    - **TRUE** - CSV statement has been generated.
    - **FALSE** - no CSV statement generated.
    """

    currency: Optional[str] = None

    currency_conversions: Optional[List[CurrencyConversion]] = FieldInfo(alias="currencyConversions", default=None)

    dt_approved: Optional[datetime] = FieldInfo(alias="dtApproved", default=None)
    """The DateTime when the bill was approved."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO 8601 format)_ when the Bill was first created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO 8601 format)_ when the Bill was last modified."""

    dt_locked: Optional[datetime] = FieldInfo(alias="dtLocked", default=None)
    """The DateTime when the bill was locked."""

    due_date: Optional[date] = FieldInfo(alias="dueDate", default=None)

    end_date: Optional[date] = FieldInfo(alias="endDate", default=None)

    end_date_time_utc: Optional[datetime] = FieldInfo(alias="endDateTimeUTC", default=None)

    external_invoice_date: Optional[date] = FieldInfo(alias="externalInvoiceDate", default=None)
    """
    For accounting purposes, the date set at Organization level to use for external
    invoicing with respect to billing periods - two options:

    - `FIRST_DAY_OF_NEXT_PERIOD` _(Default)_.
    - `LAST_DAY_OF_ARREARS`

    For example, if the retrieved Bill was on a monthly billing frequency and the
    billing period for the Bill is September 2023 and the _External invoice date_ is
    set at `FIRST_DAY_OF_NEXT_PERIOD`, then the `externalInvoiceDate` will be
    `"2023-10-01"`.

    **NOTE:** To change the `externalInvoiceDate` setting for your Organization, you
    can use the
    [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/GetOrganizationConfig)
    call.
    """

    external_invoice_reference: Optional[str] = FieldInfo(alias="externalInvoiceReference", default=None)
    """The reference ID to use for external invoice."""

    json_statement_generated: Optional[bool] = FieldInfo(alias="jsonStatementGenerated", default=None)
    """
    Flag to indicate that the statement in JSON format has been generated for the
    Bill.

    - **TRUE** - JSON statement has been generated.
    - **FALSE** - no JSON statement generated.
    """

    last_calculated_date: Optional[datetime] = FieldInfo(alias="lastCalculatedDate", default=None)

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) for the user who last modified this Bill."""

    line_items: Optional[List[LineItem]] = FieldInfo(alias="lineItems", default=None)
    """An array of the Bill line items."""

    locked: Optional[bool] = None

    locked_by: Optional[str] = FieldInfo(alias="lockedBy", default=None)
    """The id of the user who locked this bill."""

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)
    """Purchase Order number linked to the Account the Bill is for."""

    sequential_invoice_number: Optional[str] = FieldInfo(alias="sequentialInvoiceNumber", default=None)
    """The sequential invoice number of the Bill.

    **NOTE:** If you have not defined a `billPrefix` for your Organization, a
    `sequentialInvoiceNumber` is not returned in the response. See
    [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
    """

    start_date: Optional[date] = FieldInfo(alias="startDate", default=None)

    start_date_time_utc: Optional[datetime] = FieldInfo(alias="startDateTimeUTC", default=None)

    status: Optional[Literal["PENDING", "APPROVED"]] = None

    timezone: Optional[str] = None

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
