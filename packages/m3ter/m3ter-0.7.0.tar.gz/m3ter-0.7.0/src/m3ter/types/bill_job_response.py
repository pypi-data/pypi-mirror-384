# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .shared.currency_conversion import CurrencyConversion

__all__ = ["BillJobResponse"]


class BillJobResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_ids: Optional[List[str]] = FieldInfo(alias="accountIds", default=None)
    """
    An array of UUIDs representing the end customer Accounts associated with the
    BillJob.
    """

    bill_date: Optional[date] = FieldInfo(alias="billDate", default=None)
    """
    The specific billing date _(in ISO 8601 format)_, determining when the Bill was
    generated.

    For example: `"2023-01-24"`.
    """

    bill_frequency_interval: Optional[int] = FieldInfo(alias="billFrequencyInterval", default=None)
    """How often Bills are issued - used in conjunction with `billingFrequency`.

    For example, if `billingFrequency` is set to Monthly and `billFrequencyInterval`
    is set to 3, Bills are issued every three months.
    """

    bill_ids: Optional[List[str]] = FieldInfo(alias="billIds", default=None)
    """
    An array of Bill IDs related to the BillJob, providing references to the
    specific Bills generated.
    """

    billing_frequency: Optional[Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC"]] = FieldInfo(
        alias="billingFrequency", default=None
    )
    """Defines how often Bills are generated.

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

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the BillJob."""

    currency_conversions: Optional[List[CurrencyConversion]] = FieldInfo(alias="currencyConversions", default=None)
    """
    An array of currency conversion rates from Bill currency to Organization
    currency. For example, if Account is billed in GBP and Organization is set to
    USD, Bill line items are calculated in GBP and then converted to USD using the
    defined rate.
    """

    day_epoch: Optional[date] = FieldInfo(alias="dayEpoch", default=None)
    """
    The starting date _(epoch)_ for Daily billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for daily Bills.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO 8601 format)_ when the BillJob was first created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO 8601 format)_ when the BillJob was last modified."""

    due_date: Optional[date] = FieldInfo(alias="dueDate", default=None)
    """The due date _(in ISO 8601 format)_ for payment of the Bill.

    For example: `"2023-02-24"`.
    """

    external_invoice_date: Optional[date] = FieldInfo(alias="externalInvoiceDate", default=None)
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
    """

    last_date_in_billing_period: Optional[date] = FieldInfo(alias="lastDateInBillingPeriod", default=None)
    """
    Specifies the date _(in ISO 8601 format)_ of the last day in the billing period,
    defining the time range for the associated Bills.

    For example: `"2023-03-24"`.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) for the user who last modified this BillJob."""

    month_epoch: Optional[date] = FieldInfo(alias="monthEpoch", default=None)
    """
    The starting date _(epoch)_ for Monthly billing frequency _(in ISO 8601
    format)_, determining the first Bill date for monthly Bills.
    """

    pending: Optional[int] = None
    """The number of pending actions or calculations within the BillJob."""

    status: Optional[Literal["PENDING", "INITIALIZING", "RUNNING", "COMPLETE", "CANCELLED"]] = None
    """The current status of the BillJob, indicating its progress or completion state."""

    target_currency: Optional[str] = FieldInfo(alias="targetCurrency", default=None)
    """The currency code used for the Bill, such as USD, GBP, or EUR."""

    timezone: Optional[str] = None
    """
    Specifies the time zone used for the generated Bills, ensuring alignment with
    the local time zone.
    """

    total: Optional[int] = None
    """The total number of Bills or calculations related to the BillJob."""

    type: Optional[Literal["CREATE", "RECALCULATE"]] = None
    """Specifies the type of BillJob.

    - **CREATE** Returned for a _Create BillJob_ call.
    - **RECALCULATE** Returned for a successful _Create Recalculation BillJob_ call.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """

    week_epoch: Optional[date] = FieldInfo(alias="weekEpoch", default=None)
    """
    The starting date _(epoch)_ for Weekly billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for weekly Bills.
    """

    year_epoch: Optional[date] = FieldInfo(alias="yearEpoch", default=None)
    """
    The starting date _(epoch)_ for Yearly billing frequency _(in ISO 8601 format)_,
    determining the first Bill date for yearly Bills.
    """
