# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import date
from typing_extensions import Literal, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .shared_params.currency_conversion import CurrencyConversion

__all__ = ["BillJobCreateParams"]


class BillJobCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountIds")]
    """
    An array of UUIDs representing the end customer Accounts associated with the
    BillJob.
    """

    bill_date: Annotated[Union[str, date], PropertyInfo(alias="billDate", format="iso8601")]
    """
    The specific billing date _(in ISO 8601 format)_, determining when the Bill was
    generated.

    For example: `"2023-01-24"`.
    """

    bill_frequency_interval: Annotated[int, PropertyInfo(alias="billFrequencyInterval")]
    """How often Bills are issued - used in conjunction with `billingFrequency`.

    For example, if `billingFrequency` is set to Monthly and `billFrequencyInterval`
    is set to 3, Bills are issued every three months.
    """

    billing_frequency: Annotated[
        Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC"], PropertyInfo(alias="billingFrequency")
    ]
    """How often Bills are generated.

    - **Daily**. Starting at midnight each day, covering a twenty-four hour period
      following.

    - **Weekly**. Starting at midnight on a Monday morning covering the seven-day
      period following.

    - **Monthly**. Starting at midnight on the morning of the first day of each
      month covering the entire calendar month following.

    - **Annually**. Starting at midnight on the morning of the first day of each
      year covering the entire calendar year following.

    - **Ad_Hoc**. Use this setting when a custom billing schedule is used for
      billing an Account, such as for billing of Prepayment/Commitment fees using a
      custom billing schedule.
    """

    currency_conversions: Annotated[Iterable[CurrencyConversion], PropertyInfo(alias="currencyConversions")]
    """
    An array of currency conversion rates from Bill currency to Organization
    currency. For example, if Account is billed in GBP and Organization is set to
    USD, Bill line items are calculated in GBP and then converted to USD using the
    defined rate.
    """

    day_epoch: Annotated[Union[str, date], PropertyInfo(alias="dayEpoch", format="iso8601")]
    """
    The starting date _(epoch)_ for Daily billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for daily Bills.
    """

    due_date: Annotated[Union[str, date], PropertyInfo(alias="dueDate", format="iso8601")]
    """The due date _(in ISO 8601 format)_ for payment of the Bill.

    For example: `"2023-02-24"`.
    """

    external_invoice_date: Annotated[Union[str, date], PropertyInfo(alias="externalInvoiceDate", format="iso8601")]
    """
    For accounting purposes, the date set at Organization level to use for external
    invoicing with respect to billing periods - two options:

    - `FIRST_DAY_OF_NEXT_PERIOD` _(Default)_. Used when you want to recognize usage
      revenue in the following period.
    - `LAST_DAY_OF_ARREARS`. Used when you want to recognize usage revenue in the
      same period that it's consumed, instead of in the following period.

    For example, if the retrieved Bill was on a monthly billing frequency and the
    billing period for the Bill is September 2023 and the _External invoice date_ is
    set at `FIRST_DAY_OF_NEXT_PERIOD`, then the `externalInvoiceDate` will be
    `"2023-10-01"`.

    **NOTE:** To change the `externalInvoiceDate` setting for your Organization, you
    can use the
    [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/GetOrganizationConfig)
    call.
    """

    last_date_in_billing_period: Annotated[
        Union[str, date], PropertyInfo(alias="lastDateInBillingPeriod", format="iso8601")
    ]
    """
    Specifies the date _(in ISO 8601 format)_ of the last day in the billing period,
    defining the time range for the associated Bills.

    For example: `"2023-03-24"`.
    """

    month_epoch: Annotated[Union[str, date], PropertyInfo(alias="monthEpoch", format="iso8601")]
    """
    The starting date _(epoch)_ for Monthly billing frequency _(in ISO 8601
    format)_, determining the first Bill date for monthly Bills.
    """

    target_currency: Annotated[str, PropertyInfo(alias="targetCurrency")]
    """The currency code used for the Bill, such as USD, GBP, or EUR."""

    timezone: str
    """
    Specifies the time zone used for the generated Bills, ensuring alignment with
    the local time zone.
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

    week_epoch: Annotated[Union[str, date], PropertyInfo(alias="weekEpoch", format="iso8601")]
    """
    The starting date _(epoch)_ for Weekly billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for weekly Bills.
    """

    year_epoch: Annotated[Union[str, date], PropertyInfo(alias="yearEpoch", format="iso8601")]
    """
    The starting date _(epoch)_ for Yearly billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for yearly Bills.
    """
