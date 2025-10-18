# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.currency_conversion import CurrencyConversion

__all__ = ["OrganizationConfigResponse"]


class OrganizationConfigResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    auto_approve_bills_grace_period: Optional[int] = FieldInfo(alias="autoApproveBillsGracePeriod", default=None)
    """Grace period before bills are auto-approved.

    Used in combination with the field `autoApproveBillsGracePeriodUnit`.
    """

    auto_approve_bills_grace_period_unit: Optional[Literal["MINUTES", "HOURS", "DAYS"]] = FieldInfo(
        alias="autoApproveBillsGracePeriodUnit", default=None
    )

    auto_generate_statement_mode: Optional[Literal["NONE", "JSON", "JSON_AND_CSV"]] = FieldInfo(
        alias="autoGenerateStatementMode", default=None
    )
    """
    Specifies whether to auto-generate statements once Bills are _approved_ or
    _locked_. It will not auto-generate if a bill is in _pending_ state.

    The default value is **None**.

    - **None**. Statements will not be auto-generated.
    - **JSON**. Statements are auto-generated in JSON format.
    - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.
    """

    bill_prefix: Optional[str] = FieldInfo(alias="billPrefix", default=None)
    """Prefix to be used for sequential invoice numbers.

    This will be combined with the `sequenceStartNumber`.
    """

    commitment_fee_bill_in_advance: Optional[bool] = FieldInfo(alias="commitmentFeeBillInAdvance", default=None)
    """
    Specifies whether commitments _(prepayments)_ are billed in advance at the start
    of each billing period, or billed in arrears at the end of each billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    consolidate_bills: Optional[bool] = FieldInfo(alias="consolidateBills", default=None)
    """
    Specifies whether to consolidate different billing frequencies onto the same
    bill.

    - **TRUE** - consolidate different billing frequencies onto the same bill.
    - **FALSE** - bills are not consolidated.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this organization config."""

    credit_application_order: Optional[List[Literal["PREPAYMENT", "BALANCE"]]] = FieldInfo(
        alias="creditApplicationOrder", default=None
    )
    """
    The order in which any Prepayment or Balance credit amounts on Accounts are to
    be drawn-down against for billing. Four options:

    - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
      credit.
    - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
      credit.
    - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
    - `"BALANCE"`. Only draw-down against Balance credit.
    """

    currency: Optional[str] = None
    """The currency code for the currency used in this Organization.

    For example: USD, GBP, or EUR.
    """

    currency_conversions: Optional[List[CurrencyConversion]] = FieldInfo(alias="currencyConversions", default=None)
    """Currency conversion rates from Bill currency to Organization currency.

    For example, if Account is billed in GBP and Organization is set to USD, Bill
    line items are calculated in GBP and then converted to USD using the defined
    rate.
    """

    day_epoch: Optional[str] = FieldInfo(alias="dayEpoch", default=None)
    """The first bill date _(in ISO-8601 format)_ for daily billing periods."""

    days_before_bill_due: Optional[int] = FieldInfo(alias="daysBeforeBillDue", default=None)
    """
    The number of days after the Bill generation date shown on Bills as the due
    date.
    """

    default_statement_definition_id: Optional[str] = FieldInfo(alias="defaultStatementDefinitionId", default=None)
    """
    Organization level default `statementDefinitionId` to be used when there is no
    statement definition linked to the account.

    Statement definitions are used to generate bill statements, which are
    informative backing sheets to invoices.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the organization config was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The DateTime when the organization config was last modified _(in ISO-8601
    format)_.
    """

    external_invoice_date: Optional[Literal["LAST_DAY_OF_ARREARS", "FIRST_DAY_OF_NEXT_PERIOD"]] = FieldInfo(
        alias="externalInvoiceDate", default=None
    )

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this organization config."""

    minimum_spend_bill_in_advance: Optional[bool] = FieldInfo(alias="minimumSpendBillInAdvance", default=None)
    """
    Specifies whether minimum spend amounts are billed in advance at the start of
    each billing period, or billed in arrears at the end of each billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    month_epoch: Optional[str] = FieldInfo(alias="monthEpoch", default=None)
    """The first bill date _(in ISO-8601 format)_ for monthly billing periods."""

    scheduled_bill_interval: Optional[float] = FieldInfo(alias="scheduledBillInterval", default=None)
    """Specifies the required interval for updating bills.

    - **For portions of an hour (minutes)**. Two options: **0.25** (15 minutes) and
      **0.5** (30 minutes).
    - **For full hours.** Eight possible values: **1**, **2**, **3**, **4**, **6**,
      **8**, **12**, or **24**.
    - **Default.** The default is **0**, which disables scheduling.
    """

    sequence_start_number: Optional[int] = FieldInfo(alias="sequenceStartNumber", default=None)
    """The starting number to be used for sequential invoice numbers.

    This will be combined with the `billPrefix`.
    """

    standing_charge_bill_in_advance: Optional[bool] = FieldInfo(alias="standingChargeBillInAdvance", default=None)
    """
    Specifies whether the standing charge is billed in advance at the start of each
    billing period, or billed in arrears at the end of each billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    suppressed_empty_bills: Optional[bool] = FieldInfo(alias="suppressedEmptyBills", default=None)
    """Specifies whether to supress generating bills that have no line items.

    - **TRUE** - prevents generating bills with no line items.
    - **FALSE** - bills are still generated even when they have no line items.
    """

    timezone: Optional[str] = None
    """The timezone for the Organization."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

    week_epoch: Optional[str] = FieldInfo(alias="weekEpoch", default=None)
    """The first bill date _(in ISO-8601 format)_ for weekly billing periods."""

    year_epoch: Optional[str] = FieldInfo(alias="yearEpoch", default=None)
    """The first bill date _(in ISO-8601 format)_ for yearly billing periods."""
