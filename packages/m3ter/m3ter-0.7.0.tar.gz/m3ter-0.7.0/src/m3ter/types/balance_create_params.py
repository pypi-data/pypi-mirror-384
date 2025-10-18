# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["BalanceCreateParams"]


class BalanceCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """The unique identifier (UUID) for the end customer Account."""

    currency: Required[str]
    """The currency code used for the Balance amount. For example: USD, GBP or EUR."""

    end_date: Required[Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]]
    """
    The date _(in ISO 8601 format)_ after which the Balance will no longer be active
    for the Account.

    **Note:** You can use the `rolloverEndDate` request parameter to define an
    extended grace period for continued draw-down against the Balance if any amount
    remains when the specified `endDate` is reached.
    """

    start_date: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]]
    """The date _(in ISO 8601 format)_ when the Balance becomes active."""

    balance_draw_down_description: Annotated[str, PropertyInfo(alias="balanceDrawDownDescription")]
    """A description for the bill line items for draw-down charges against the Balance.

    _(Optional)._
    """

    code: str
    """Unique short code for the Balance."""

    consumptions_accounting_product_id: Annotated[str, PropertyInfo(alias="consumptionsAccountingProductId")]
    """
    Optional Product ID this Balance Consumptions should be attributed to for
    accounting purposes
    """

    contract_id: Annotated[str, PropertyInfo(alias="contractId")]

    custom_fields: Annotated[Dict[str, Union[str, float]], PropertyInfo(alias="customFields")]
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level, `customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    description: str
    """A description of the Balance."""

    fees_accounting_product_id: Annotated[str, PropertyInfo(alias="feesAccountingProductId")]
    """
    Optional Product ID this Balance Fees should be attributed to for accounting
    purposes
    """

    line_item_types: Annotated[
        List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ],
        PropertyInfo(alias="lineItemTypes"),
    ]
    """
    Specify the line item charge types that can draw-down at billing against the
    Balance amount. Options are:

    - `"MINIMUM_SPEND"`
    - `"STANDING_CHARGE"`
    - `"USAGE"`
    - `"COUNTER_RUNNING_TOTAL_CHARGE"`
    - `"COUNTER_ADJUSTMENT_DEBIT"`

    **NOTE:** If no charge types are specified, by default _all types_ can draw-down
    against the Balance amount at billing.
    """

    name: str
    """The official name for the Balance."""

    overage_description: Annotated[str, PropertyInfo(alias="overageDescription")]
    """A description for Bill line items overage charges."""

    overage_surcharge_percent: Annotated[float, PropertyInfo(alias="overageSurchargePercent")]
    """
    Define a surcharge level, as a percentage of regular usage rating, applied to
    overages _(usage charges that exceed the Balance amount)_. For example, if the
    regular usage rate is $10 per unit of usage consumed and
    `overageSurchargePercent` is set at 10%, then any usage charged above the
    original Balance amount is charged at $11 per unit of usage.
    """

    product_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="productIds")]
    """
    Specify the Products whose consumption charges due at billing can be drawn-down
    against the Balance amount.

    **Note:** If you don't specify any Products for Balance draw-down, by default
    the consumption charges for any Product the Account consumes will be drawn-down
    against the Balance amount.
    """

    rollover_amount: Annotated[float, PropertyInfo(alias="rolloverAmount")]
    """
    The maximum amount that can be carried over past the Balance end date for
    draw-down at billing if there is any unused Balance amount when the end date is
    reached. Works with `rolloverEndDate` to define the amount and duration of a
    Balance "grace period". _(Optional)_

    **Notes:**

    - If you leave `rolloverAmount` empty and only enter a `rolloverEndDate`, any
      amount left over after the Balance end date is reached will be drawn-down
      against up to the specified `rolloverEndDate`.
    - You must enter a `rolloverEndDate`. If you only enter a `rolloverAmount`
      without entering a `rolloverEndDate`, you'll receive an error when trying to
      create or update the Balance.
    - If you don't want to grant any grace period for outstanding Balance amounts,
      then do not use `rolloverAmount` and `rolloverEndDate`.
    """

    rollover_end_date: Annotated[Union[str, datetime], PropertyInfo(alias="rolloverEndDate", format="iso8601")]
    """
    The end date _(in ISO 8601 format)_ for the grace period during which unused
    Balance amounts can be carried over and drawn-down against at billing.

    **Note:** Use `rolloverAmount` if you want to specify a maximum amount that can
    be carried over and made available for draw-down.
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
