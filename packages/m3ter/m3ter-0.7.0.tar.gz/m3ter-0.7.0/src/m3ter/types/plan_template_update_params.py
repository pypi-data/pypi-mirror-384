# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["PlanTemplateUpdateParams"]


class PlanTemplateUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bill_frequency: Required[
        Annotated[
            Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"], PropertyInfo(alias="billFrequency")
        ]
    ]
    """Determines the frequency at which bills are generated.

    - **Daily**. Starting at midnight each day, covering the twenty-four hour period
      following.

    - **Weekly**. Starting at midnight on a Monday, covering the seven-day period
      following.

    - **Monthly**. Starting at midnight on the first day of each month, covering the
      entire calendar month following.

    - **Annually**. Starting at midnight on first day of each year covering the
      entire calendar year following.
    """

    currency: Required[str]
    """
    The ISO currency code for the currency used to charge end users - for example
    USD, GBP, EUR. This defines the _pricing currency_ and is inherited by any Plans
    based on the Plan Template.

    **Notes:**

    - You can define a currency at Organization-level or Account-level to be used as
      the _billing currency_. This can be a different currency to that used for the
      Plan as the _pricing currency_.
    - If the billing currency for an Account is different to the pricing currency
      used by a Plan attached to the Account, you must ensure a _currency conversion
      rate_ is defined for your Organization to convert the pricing currency into
      the billing currency at billing, otherwise Bills will fail for the Account.
    - To define any required currency conversion rates, use the
      `currencyConversions` request body parameter for the
      [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
      call.
    """

    name: Required[str]
    """Descriptive name for the PlanTemplate."""

    product_id: Required[Annotated[str, PropertyInfo(alias="productId")]]
    """The unique identifier (UUID) of the Product associated with this PlanTemplate."""

    standing_charge: Required[Annotated[float, PropertyInfo(alias="standingCharge")]]
    """The fixed charge _(standing charge)_ applied to customer bills.

    This charge is prorated and must be a non-negative number.
    """

    bill_frequency_interval: Annotated[int, PropertyInfo(alias="billFrequencyInterval")]
    """How often bills are issued.

    For example, if `billFrequency` is Monthly and `billFrequencyInterval` is 3,
    bills are issued every three months.
    """

    code: str
    """A unique, short code reference for the PlanTemplate.

    This code should not contain control characters or spaces.
    """

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

    minimum_spend: Annotated[float, PropertyInfo(alias="minimumSpend")]
    """
    The Product minimum spend amount per billing cycle for end customer Accounts on
    a pricing Plan based on the PlanTemplate. This must be a non-negative number.
    """

    minimum_spend_bill_in_advance: Annotated[bool, PropertyInfo(alias="minimumSpendBillInAdvance")]
    """A boolean that determines when the minimum spend is billed.

    - TRUE - minimum spend is billed at the start of each billing period.
    - FALSE - minimum spend is billed at the end of each billing period.

    Overrides the setting at Organizational level for minimum spend billing in
    arrears/in advance.
    """

    minimum_spend_description: Annotated[str, PropertyInfo(alias="minimumSpendDescription")]
    """Minimum spend description _(displayed on the bill line item)_."""

    ordinal: int
    """The ranking of the PlanTemplate among your pricing plans.

    Lower numbers represent more basic plans, while higher numbers represent premium
    plans. This must be a non-negative integer.

    **NOTE: DEPRECATED** - do not use.
    """

    standing_charge_bill_in_advance: Annotated[bool, PropertyInfo(alias="standingChargeBillInAdvance")]
    """A boolean that determines when the standing charge is billed.

    - TRUE - standing charge is billed at the start of each billing period.
    - FALSE - standing charge is billed at the end of each billing period.

    Overrides the setting at Organizational level for standing charge billing in
    arrears/in advance.
    """

    standing_charge_description: Annotated[str, PropertyInfo(alias="standingChargeDescription")]
    """Standing charge description _(displayed on the bill line item)_."""

    standing_charge_interval: Annotated[int, PropertyInfo(alias="standingChargeInterval")]
    """How often the standing charge is applied.

    For example, if the bill is issued every three months and
    `standingChargeInterval` is 2, then the standing charge is applied every six
    months.
    """

    standing_charge_offset: Annotated[int, PropertyInfo(alias="standingChargeOffset")]
    """Defines an offset for when the standing charge is first applied.

    For example, if the bill is issued every three months and the
    `standingChargeOfset` is 0, then the charge is applied to the first bill _(at
    three months)_; if 1, it would be applied to the second bill _(at six months)_,
    and so on.
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
