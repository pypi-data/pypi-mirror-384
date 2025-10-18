# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .commitment_fee import CommitmentFee

__all__ = ["CommitmentResponse"]


class CommitmentResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """
    The unique identifier (UUID) for the end customer Account the Commitment is
    added to.
    """

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)
    """
    The unique identifier (UUID) for the Product linked to the Commitment for
    accounting purposes.
    """

    amount: Optional[float] = None
    """The total amount that the customer has committed to pay."""

    amount_first_bill: Optional[float] = FieldInfo(alias="amountFirstBill", default=None)
    """The amount to be billed in the first invoice."""

    amount_pre_paid: Optional[float] = FieldInfo(alias="amountPrePaid", default=None)
    """
    The amount that the customer has already paid upfront at the start of the
    Commitment service period.
    """

    amount_spent: Optional[float] = FieldInfo(alias="amountSpent", default=None)
    """The total amount of the Commitment that the customer has spent so far."""

    bill_epoch: Optional[date] = FieldInfo(alias="billEpoch", default=None)
    """
    The starting date _(in ISO-8601 date format)_ from which the billing cycles are
    calculated.
    """

    billing_interval: Optional[int] = FieldInfo(alias="billingInterval", default=None)
    """How often the Commitment fees are applied to bills.

    For example, if the plan being used to bill for Commitment fees is set to issue
    bills every three months and the `billingInterval` is set to 2, then the
    Commitment fees are applied every six months.
    """

    billing_offset: Optional[int] = FieldInfo(alias="billingOffset", default=None)
    """
    The offset for when the Commitment fees are first applied to bills on the
    Account. For example, if bills are issued every three months and the
    `billingOffset` is 0, then the charge is applied to the first bill (at three
    months); if set to 1, it's applied to the next bill (at six months), and so on.
    """

    billing_plan_id: Optional[str] = FieldInfo(alias="billingPlanId", default=None)
    """
    The unique identifier (UUID) for the Product Plan used for billing Commitment
    fees due.
    """

    child_billing_mode: Optional[Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"]] = FieldInfo(
        alias="childBillingMode", default=None
    )
    """
    If the Account is either a Parent or a Child Account, this specifies the Account
    hierarchy billing mode. The mode determines how billing will be handled and
    shown on bills for charges due on the Parent Account, and charges due on Child
    Accounts:

    - **Parent Breakdown** - a separate bill line item per Account. Default setting.

    - **Parent Summary** - single bill line item for all Accounts.

    - **Child** - the Child Account is billed.
    """

    commitment_fee_bill_in_advance: Optional[bool] = FieldInfo(alias="commitmentFeeBillInAdvance", default=None)
    """
    A boolean value indicating whether the Commitment fee is billed in advance
    _(start of each billing period)_ or arrears _(end of each billing period)_.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    commitment_fee_description: Optional[str] = FieldInfo(alias="commitmentFeeDescription", default=None)
    """A textual description of the Commitment fee."""

    commitment_usage_description: Optional[str] = FieldInfo(alias="commitmentUsageDescription", default=None)
    """A textual description of the Commitment usage."""

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)
    """
    The unique identifier (UUID) for a Contract you've created for the Account and
    to which the Commitment has been added.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Commitment."""

    currency: Optional[str] = None
    """The currency used for the Commitment. For example, 'USD'."""

    drawdowns_accounting_product_id: Optional[str] = FieldInfo(alias="drawdownsAccountingProductId", default=None)

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the Commitment was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO-8601 format)_ when the Commitment was last modified."""

    end_date: Optional[date] = FieldInfo(alias="endDate", default=None)
    """The end date of the Commitment period in ISO-8601 format."""

    fee_dates: Optional[List[CommitmentFee]] = FieldInfo(alias="feeDates", default=None)
    """Used for billing any outstanding Commitment fees _on a schedule_.

    An array defining a series of bill dates and amounts covering specified service
    periods:

    - `date` - the billing date _(in ISO-8601 format)_.
    - `amount` - the billed amount.
    - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
      period the bill covers _(in ISO-8601 format)_.
    """

    fees_accounting_product_id: Optional[str] = FieldInfo(alias="feesAccountingProductId", default=None)

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this Commitment."""

    line_item_types: Optional[
        List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ]
    ] = FieldInfo(alias="lineItemTypes", default=None)
    """
    Specifies the line item charge types that can draw-down at billing against the
    Commitment amount. Options are:

    - `MINIMUM_SPEND`
    - `STANDING_CHARGE`
    - `USAGE`
    - `"COUNTER_RUNNING_TOTAL_CHARGE"`
    - `"COUNTER_ADJUSTMENT_DEBIT"`
    """

    overage_description: Optional[str] = FieldInfo(alias="overageDescription", default=None)
    """A textual description of the overage charges."""

    overage_surcharge_percent: Optional[float] = FieldInfo(alias="overageSurchargePercent", default=None)
    """
    The percentage surcharge applied to the usage charges that exceed the Commitment
    amount.
    """

    product_ids: Optional[List[str]] = FieldInfo(alias="productIds", default=None)
    """A list of unique identifiers (UUIDs) for Products the Account consumes.

    Charges due for these Products will be made available for draw-down against the
    Commitment.

    **Note:** If not used, then charges due for all Products the Account consumes
    will be made available for draw-down against the Commitment.
    """

    separate_overage_usage: Optional[bool] = FieldInfo(alias="separateOverageUsage", default=None)
    """
    A boolean value indicating whether the overage usage is billed separately or
    together. If overage usage is separated and a Commitment amount has been
    consumed by an Account, any subsequent line items on Bills against the Account
    for usage will show as separate "overage usage" charges, not simply as "usage"
    charges:

    - **TRUE** - billed separately.
    - **FALSE** - billed together.
    """

    start_date: Optional[date] = FieldInfo(alias="startDate", default=None)
    """The start date of the Commitment period in ISO-8601 format."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
