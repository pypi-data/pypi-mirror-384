# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .shared_params.currency_conversion import CurrencyConversion

__all__ = ["OrganizationConfigUpdateParams"]


class OrganizationConfigUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    currency: Required[str]
    """The currency code for the Organization. For example: USD, GBP, or EUR:

    - This defines the _billing currency_ for the Organization. You can override
      this by selecting a different billing currency at individual Account level.
    - You must first define the currencies you want to use in your Organization. See
      the [Currency](https://www.m3ter.com/docs/api#tag/Currency) section in this
      API Reference.

    **Note:** If you use a different currency as the _pricing currency_ for Plans to
    set charge rates for Product consumption by an Account, you must define a
    currency conversion rate from the pricing currency to the billing currency
    before you run billing for the Account, otherwise billing will fail. See below
    for the `currencyConversions` request parameter.
    """

    day_epoch: Required[Annotated[str, PropertyInfo(alias="dayEpoch")]]
    """
    Optional setting that defines the billing cycle date for Accounts that are
    billed daily. Defines the date of the first Bill:

    - For example, suppose the Plan you attach to an Account is configured for daily
      billing frequency and will apply to the Account from January 1st, 2022 until
      June 30th, 2022. If you set a `dayEpoch` date of January 2nd, 2022, then the
      first Bill is created for the Account on that date and subsequent Bills are
      created for the Account each day following through to the end of the billing
      service period.
    - The date is in ISO-8601 format.
    """

    days_before_bill_due: Required[Annotated[int, PropertyInfo(alias="daysBeforeBillDue")]]
    """
    Enter the number of days after the Bill generation date that you want to show on
    Bills as the due date.

    **Note:** If you define `daysBeforeBillDue` at individual Account level, this
    will take precedence over any `daysBeforeBillDue` setting defined at
    Organization level.
    """

    month_epoch: Required[Annotated[str, PropertyInfo(alias="monthEpoch")]]
    """
    Optional setting that defines the billing cycle date for Accounts that are
    billed monthly. Defines the date of the first Bill and then acts as reference
    for when subsequent Bills are created for the Account:

    - For example, suppose the Plan you attach to an Account is configured for
      monthly billing frequency and will apply to the Account from January 1st, 2022
      until June 30th, 2022. If you set a `monthEpoch` date of January 15th, 2022,
      then the first Bill is created for the Account on that date and subsequent
      Bills are created for the Account on the 15th of each month following through
      to the end of the billing service period - February 15th, March 15th, and so
      on.
    - The date is in ISO-8601 format.
    """

    timezone: Required[str]
    """Sets the timezone for the Organization."""

    week_epoch: Required[Annotated[str, PropertyInfo(alias="weekEpoch")]]
    """
    Optional setting that defines the billing cycle date for Accounts that are
    billed weekly. Defines the date of the first Bill and then acts as reference for
    when subsequent Bills are created for the Account:

    - For example, suppose the Plan you attach to an Account is configured for
      weekly billing frequency and will apply to the Account from January 1st, 2022
      until June 30th, 2022. If you set a `weekEpoch` date of January 15th, 2022,
      which falls on a Saturday, then the first Bill is created for the Account on
      that date and subsequent Bills are created for the Account on Saturday of each
      week following through to the end of the billing service period.
    - The date is in ISO-8601 format.
    """

    year_epoch: Required[Annotated[str, PropertyInfo(alias="yearEpoch")]]
    """
    Optional setting that defines the billing cycle date for Accounts that are
    billed yearly. Defines the date of the first Bill and then acts as reference for
    when subsequent Bills are created for the Account:

    - For example, suppose the Plan you attach to an Account is configured for
      yearly billing frequency and will apply to the Account from January 1st, 2022
      until January 15th, 2028. If you set a `yearEpoch` date of January 1st, 2023,
      then the first Bill is created for the Account on that date and subsequent
      Bills are created for the Account on January 1st of each year following
      through to the end of the billing service period - January 1st, 2023, January
      1st, 2024 and so on.
    - The date is in ISO-8601 format.
    """

    auto_approve_bills_grace_period: Annotated[int, PropertyInfo(alias="autoApproveBillsGracePeriod")]
    """Grace period before bills are auto-approved.

    Used in combination with `autoApproveBillsGracePeriodUnit` parameter.

    **Note:** When used in combination with `autoApproveBillsGracePeriodUnit`
    enables auto-approval of Bills for Organization, which occurs when the specified
    time period has elapsed after Bill generation.
    """

    auto_approve_bills_grace_period_unit: Annotated[str, PropertyInfo(alias="autoApproveBillsGracePeriodUnit")]
    """Time unit of grace period before bills are auto-approved.

    Used in combination with `autoApproveBillsGracePeriod` parameter. Allowed
    options are MINUTES, HOURS, or DAYS.

    **Note:** When used in combination with `autoApproveBillsGracePeriod` enables
    auto-approval of Bills for Organization, which occurs when the specified time
    period has elapsed after Bill generation.
    """

    auto_generate_statement_mode: Annotated[
        Literal["NONE", "JSON", "JSON_AND_CSV"], PropertyInfo(alias="autoGenerateStatementMode")
    ]
    """
    Specify whether to auto-generate statements once Bills are _approved_ or
    _locked_. It will not auto-generate if a bill is in _pending_ state.

    The default value is **None**.

    - **None**. Statements will not be auto-generated.
    - **JSON**. Statements are auto-generated in JSON format.
    - **JSON and CSV**. Statements are auto-generated in both JSON and CSV formats.
    """

    bill_prefix: Annotated[str, PropertyInfo(alias="billPrefix")]
    """Prefix to be used for sequential invoice numbers.

    This will be combined with the `sequenceStartNumber`.

    **NOTES:**

    - If you do not define a `billPrefix`, a default will be used in the Console for
      the Bill **REFERENCE** number. This default will concatenate **INV-** with the
      last four characters of the `billId`.
    - If you do not define a `billPrefix`, the Bill response schema for API calls
      that retrieve Bill data will not contain a `sequentialInvoiceNumber`.
    """

    commitment_fee_bill_in_advance: Annotated[bool, PropertyInfo(alias="commitmentFeeBillInAdvance")]
    """
    Boolean setting to specify whether commitments _(prepayments)_ are billed in
    advance at the start of each billing period, or billed in arrears at the end of
    each billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    consolidate_bills: Annotated[bool, PropertyInfo(alias="consolidateBills")]
    """Boolean setting to consolidate different billing frequencies onto the same bill.

    - **TRUE** - consolidate different billing frequencies onto the same bill.
    - **FALSE** - bills are not consolidated.
    """

    credit_application_order: Annotated[
        List[Literal["PREPAYMENT", "BALANCE"]], PropertyInfo(alias="creditApplicationOrder")
    ]
    """
    Define the order in which any Prepayment or Balance amounts on Accounts are to
    be drawn-down against for billing. Four options:

    - `"PREPAYMENT","BALANCE"`. Draw-down against Prepayment credit before Balance
      credit.
    - `"BALANCE","PREPAYMENT"`. Draw-down against Balance credit before Prepayment
      credit.
    - `"PREPAYMENT"`. Only draw-down against Prepayment credit.
    - `"BALANCE"`. Only draw-down against Balance credit.

    **NOTES:**

    - You can override this Organization-level setting for `creditApplicationOrder`
      at the level of an individual Account.
    - If the Account belongs to a Parent/Child Account hierarchy, then the
      `creditApplicationOrder` settings are not available, and the draw-down order
      defaults always to Prepayment then Balance order.
    """

    currency_conversions: Annotated[Iterable[CurrencyConversion], PropertyInfo(alias="currencyConversions")]
    """Define currency conversion rates from _pricing currency_ to _billing currency_:

    - You can use the `currency` request parameter with this call to define the
      billing currency for your Organization - see above.
    - You can also define a billing currency at the individual Account level and
      this will override the Organization billing currency.
    - A Plan used to set Product consumption charge rates on an Account might use a
      different pricing currency. At billing, charges are calculated in the pricing
      currency and then converted into billing currency amounts to appear on Bills.
      If you haven't defined a currency conversion rate from pricing to billing
      currency, billing will fail for the Account.
    """

    default_statement_definition_id: Annotated[str, PropertyInfo(alias="defaultStatementDefinitionId")]
    """
    Organization level default `statementDefinitionId` to be used when there is no
    statement definition linked to the account.

    Statement definitions are used to generate bill statements, which are
    informative backing sheets to invoices.
    """

    external_invoice_date: Annotated[str, PropertyInfo(alias="externalInvoiceDate")]
    """Date to use for the invoice date.

    Allowed values are `FIRST_DAY_OF_NEXT_PERIOD` or `LAST_DAY_OF_ARREARS`.
    """

    minimum_spend_bill_in_advance: Annotated[bool, PropertyInfo(alias="minimumSpendBillInAdvance")]
    """
    Boolean setting to specify whether minimum spend amounts are billed in advance
    at the start of each billing period, or billed in arrears at the end of each
    billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    scheduled_bill_interval: Annotated[float, PropertyInfo(alias="scheduledBillInterval")]
    """Sets the required interval for updating bills.

    It is an optional parameter that can be set as:

    - **For portions of an hour (minutes)**. Two options: **0.25** (15 minutes) and
      **0.5** (30 minutes).
    - **For full hours.** Enter **1** for every hour, **2** for every two hours, and
      so on. Eight options: **1**, **2**, **3**, **4**, **6**, **8**, **12**, or
      **24**.
    - **Default.** The default is **0**, which disables scheduling.
    """

    sequence_start_number: Annotated[int, PropertyInfo(alias="sequenceStartNumber")]
    """The starting number to be used for sequential invoice numbers.

    This will be combined with the `billPrefix`.

    For example, if you define `billPrefix` to be **INVOICE-** and you set the
    `seqenceStartNumber` as **100**, the first Bill created after updating your
    Organization Configuration will have a `sequentialInvoiceNumber` assigned of
    **INVOICE-101**. Subsequent Bills created will be numbered in time sequence for
    their initial creation date/time.
    """

    standing_charge_bill_in_advance: Annotated[bool, PropertyInfo(alias="standingChargeBillInAdvance")]
    """
    Boolean setting to specify whether the standing charge is billed in advance at
    the start of each billing period, or billed in arrears at the end of each
    billing period.

    - **TRUE** - bill in advance _(start of each billing period)_.
    - **FALSE** - bill in arrears _(end of each billing period)_.
    """

    suppressed_empty_bills: Annotated[bool, PropertyInfo(alias="suppressedEmptyBills")]
    """Boolean setting that supresses generating bills that have no line items.

    - **TRUE** - prevents generating bills with no line items.
    - **FALSE** - bills are still generated even when they have no line items.
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
