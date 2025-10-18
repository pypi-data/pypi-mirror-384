# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["PlanGroupUpdateParams"]


class PlanGroupUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    currency: Required[str]
    """Currency code for the PlanGroup (For example, USD)."""

    name: Required[str]
    """The name of the PlanGroup."""

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """Optional.

    This PlanGroup is created as bespoke for the associated Account with this
    Account ID.
    """

    code: str
    """The short code representing the PlanGroup."""

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
    """The minimum spend amount for the PlanGroup."""

    minimum_spend_accounting_product_id: Annotated[str, PropertyInfo(alias="minimumSpendAccountingProductId")]
    """Optional.

    Product ID to attribute the PlanGroup's minimum spend for accounting purposes.
    """

    minimum_spend_bill_in_advance: Annotated[bool, PropertyInfo(alias="minimumSpendBillInAdvance")]
    """A boolean flag that determines when the minimum spend is billed.

    This flag overrides the setting at Organizational level for minimum spend
    billing in arrears/in advance.

    - **TRUE** - minimum spend is billed at the start of each billing period.
    - **FALSE** - minimum spend is billed at the end of each billing period.
    """

    minimum_spend_description: Annotated[str, PropertyInfo(alias="minimumSpendDescription")]
    """Description of the minimum spend, displayed on the bill line item."""

    standing_charge: Annotated[float, PropertyInfo(alias="standingCharge")]
    """Standing charge amount for the PlanGroup."""

    standing_charge_accounting_product_id: Annotated[str, PropertyInfo(alias="standingChargeAccountingProductId")]
    """Optional.

    Product ID to attribute the PlanGroup's standing charge for accounting purposes.
    """

    standing_charge_bill_in_advance: Annotated[bool, PropertyInfo(alias="standingChargeBillInAdvance")]
    """A boolean flag that determines when the standing charge is billed.

    This flag overrides the setting at Organizational level for standing charge
    billing in arrears/in advance.

    - **TRUE** - standing charge is billed at the start of each billing period.
    - **FALSE** - standing charge is billed at the end of each billing period.
    """

    standing_charge_description: Annotated[str, PropertyInfo(alias="standingChargeDescription")]
    """Description of the standing charge, displayed on the bill line item."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
