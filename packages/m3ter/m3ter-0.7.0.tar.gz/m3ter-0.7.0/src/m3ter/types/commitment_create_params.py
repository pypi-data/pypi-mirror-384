# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable
from datetime import date
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .commitment_fee_param import CommitmentFeeParam

__all__ = ["CommitmentCreateParams"]


class CommitmentCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """
    The unique identifier (UUID) for the end customer Account the Commitment is
    added to.
    """

    amount: Required[float]
    """The total amount that the customer has committed to pay."""

    currency: Required[str]
    """The currency used for the Commitment. For example: USD."""

    end_date: Required[Annotated[Union[str, date], PropertyInfo(alias="endDate", format="iso8601")]]
    """The end date of the Commitment period in ISO-8601 format.

    **Note:** End date is exclusive - if you set an end date of June 1st 2022, then
    the Commitment ceases to be active for the Account at midnight on May 31st 2022,
    and any Prepayment fees due are calculated up to that point in time, NOT up to
    midnight on June 1st
    """

    start_date: Required[Annotated[Union[str, date], PropertyInfo(alias="startDate", format="iso8601")]]
    """The start date of the Commitment period in ISO-8601 format."""

    accounting_product_id: Annotated[str, PropertyInfo(alias="accountingProductId")]
    """
    The unique identifier (UUID) for the Product linked to the Commitment for
    accounting purposes. _(Optional)_

    **NOTE:** If you're planning to set up an integration for sending Bills to an
    external accounts receivable system, please check requirements for your chosen
    system. Some systems, such as NetSuite, require a Product to be linked with any
    Bill line items associated with Account Commitments, and the integration will
    fail if this is not present
    """

    amount_first_bill: Annotated[float, PropertyInfo(alias="amountFirstBill")]
    """The amount to be billed in the first invoice."""

    amount_pre_paid: Annotated[float, PropertyInfo(alias="amountPrePaid")]
    """
    The amount that the customer has already paid upfront at the start of the
    Commitment service period.
    """

    bill_epoch: Annotated[Union[str, date], PropertyInfo(alias="billEpoch", format="iso8601")]
    """
    The starting date _(in ISO-8601 date format)_ from which the billing cycles are
    calculated.
    """

    billing_interval: Annotated[int, PropertyInfo(alias="billingInterval")]
    """How often the Commitment fees are applied to bills.

    For example, if the plan being used to bill for Commitment fees is set to issue
    bills every three months and the `billingInterval` is set to 2, then the
    Commitment fees are applied every six months.
    """

    billing_offset: Annotated[int, PropertyInfo(alias="billingOffset")]
    """
    Defines an offset for when the Commitment fees are first applied to bills on the
    Account. For example, if bills are issued every three months and the
    `billingOffset` is 0, then the charge is applied to the first bill (at three
    months); if set to 1, it's applied to the next bill (at six months), and so on.
    """

    billing_plan_id: Annotated[str, PropertyInfo(alias="billingPlanId")]
    """
    The unique identifier (UUID) for the Product Plan used for billing Commitment
    fees due.
    """

    child_billing_mode: Annotated[
        Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"], PropertyInfo(alias="childBillingMode")
    ]
    """
    If the Account is either a Parent or a Child Account, this specifies the Account
    hierarchy billing mode. The mode determines how billing will be handled and
    shown on bills for charges due on the Parent Account, and charges due on Child
    Accounts:

    - **Parent Breakdown** - a separate bill line item per Account. Default setting.

    - **Parent Summary** - single bill line item for all Accounts.

    - **Child** - the Child Account is billed.
    """

    commitment_fee_bill_in_advance: Annotated[bool, PropertyInfo(alias="commitmentFeeBillInAdvance")]
    """
    A boolean value indicating whether the Commitment fee is billed in advance
    _(start of each billing period)_ or arrears _(end of each billing period)_.

    If no value is supplied, then the Organization Configuration value is used.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    commitment_fee_description: Annotated[str, PropertyInfo(alias="commitmentFeeDescription")]
    """A textual description of the Commitment fee."""

    commitment_usage_description: Annotated[str, PropertyInfo(alias="commitmentUsageDescription")]
    """A textual description of the Commitment usage."""

    contract_id: Annotated[str, PropertyInfo(alias="contractId")]
    """
    The unique identifier (UUID) for a Contract you've created for the Account -
    used to add the Commitment to this Contract.

    **Note:** If you associate the Commitment with a Contract you must ensure the
    Account Plan attached to the Account has the same Contract associated with it.
    If the Account Plan Contract and Commitment Contract do not match, then at
    billing the Commitment amount will not be drawn-down against.
    """

    drawdowns_accounting_product_id: Annotated[str, PropertyInfo(alias="drawdownsAccountingProductId")]
    """
    Optional Product ID this Commitment consumptions should be attributed to for
    accounting purposes
    """

    fee_dates: Annotated[Iterable[CommitmentFeeParam], PropertyInfo(alias="feeDates")]
    """Used for billing any outstanding Commitment fees _on a schedule_.

    Create an array to define a series of bill dates and amounts covering specified
    service periods:

    - `date` - the billing date _(in ISO-8601 format)_.
    - `amount` - the billed amount.
    - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
      period the bill covers _(in ISO-8601 format)_.

    **Notes:**

    - If you try to set `servicePeriodStartDate` _after_ `servicePeriodEndDate`,
      you'll receive an error.
    - You can set `servicePeriodStartDate` and `servicePeriodEndDate` to the _same
      date_ without receiving an error, but _please be sure_ your Commitment billing
      use case requires this.
    """

    fees_accounting_product_id: Annotated[str, PropertyInfo(alias="feesAccountingProductId")]
    """
    Optional Product ID this Commitment fees should be attributed to for accounting
    purposes
    """

    line_item_types: Annotated[
        List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ],
        PropertyInfo(alias="lineItemTypes"),
    ]
    """
    Specify the line item charge types that can draw-down at billing against the
    Commitment amount. Options are:

    - `MINIMUM_SPEND`
    - `STANDING_CHARGE`
    - `USAGE`
    - `"COUNTER_RUNNING_TOTAL_CHARGE"`
    - `"COUNTER_ADJUSTMENT_DEBIT"`

    **NOTE:** If no charge types are specified, by default _all types_ can draw-down
    against the Commitment amount at billing.
    """

    overage_description: Annotated[str, PropertyInfo(alias="overageDescription")]
    """A textual description of the overage charges."""

    overage_surcharge_percent: Annotated[float, PropertyInfo(alias="overageSurchargePercent")]
    """
    The percentage surcharge applied to usage charges that exceed the Commitment
    amount.

    **Note:** You can enter a _negative percentage_ if you want to give a discount
    rate for usage to end customers who exceed their Commitment amount
    """

    product_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="productIds")]
    """A list of unique identifiers (UUIDs) for Products the Account consumes.

    Charges due for these Products will be made available for draw-down against the
    Commitment.

    **Note:** If not used, then charges due for all Products the Account consumes
    will be made available for draw-down against the Commitment.
    """

    separate_overage_usage: Annotated[bool, PropertyInfo(alias="separateOverageUsage")]
    """
    A boolean value indicating whether the overage usage is billed separately or
    together. If overage usage is separated and a Commitment amount has been
    consumed by an Account, any subsequent line items on Bills against the Account
    for usage will show as separate "overage usage" charges, not simply as "usage"
    charges:

    - **TRUE** - billed separately.
    - **FALSE** - billed together.

    **Notes:**

    - Can be used only if no value or 0 has been defined for the
      `overageSurchargePercent` parameter. If you try to separate overage usage when
      a value other than 0 has been defined for `overageSurchargePercent`, you'll
      receive an error.
    - If a priced Plan is used to bill any outstanding Commitment fees due and the
      Plan is set up with overage pricing on a _tiered pricing structure_ and you
      enable separate bill line items for overage usage, then overage usage charges
      will be rated according to the overage pricing defined for the tiered pricing
      on the Plan.
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
