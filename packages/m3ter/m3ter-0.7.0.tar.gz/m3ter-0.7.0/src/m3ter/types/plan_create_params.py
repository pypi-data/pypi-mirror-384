# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["PlanCreateParams"]


class PlanCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    code: Required[str]
    """Unique short code reference for the Plan."""

    name: Required[str]
    """Descriptive name for the Plan."""

    plan_template_id: Required[Annotated[str, PropertyInfo(alias="planTemplateId")]]
    """UUID of the PlanTemplate the Plan belongs to."""

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """_(Optional)_.

    Used to specify an Account for which the Plan will be a custom/bespoke Plan:

    - Use when first creating a Plan.
    - A custom/bespoke Plan can only be attached to the specified Account.
    - Once created, a custom/bespoke Plan cannot be updated to be made a
      custom/bespoke Plan for a different Account.
    """

    bespoke: bool
    """
    TRUE/FALSE flag indicating whether the plan is a custom/bespoke Plan for a
    particular Account:

    - When creating a Plan, use the `accountId` request parameter to specify the
      Account for which the Plan will be custom/bespoke.
    - A custom/bespoke Plan can only be attached to the specified Account.
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
    The product minimum spend amount per billing cycle for end customer Accounts on
    a priced Plan.

    _(Optional)_. Overrides PlanTemplate value.
    """

    minimum_spend_accounting_product_id: Annotated[str, PropertyInfo(alias="minimumSpendAccountingProductId")]
    """
    Optional Product ID this plan's minimum spend should be attributed to for
    accounting purposes
    """

    minimum_spend_bill_in_advance: Annotated[bool, PropertyInfo(alias="minimumSpendBillInAdvance")]
    """When TRUE, minimum spend is billed at the start of each billing period.

    When FALSE, minimum spend is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
    billing in arrears/in advance.
    """

    minimum_spend_description: Annotated[str, PropertyInfo(alias="minimumSpendDescription")]
    """Minimum spend description _(displayed on the bill line item)_."""

    ordinal: int
    """
    Assigns a rank or position to the Plan in your order of pricing plans - lower
    numbers represent more basic pricing plans; higher numbers represent more
    premium pricing plans.

    _(Optional)_. Overrides PlanTemplate value.

    **NOTE: DEPRECATED** - do not use.
    """

    standing_charge: Annotated[float, PropertyInfo(alias="standingCharge")]
    """The standing charge applied to bills for end customers. This is prorated.

    _(Optional)_. Overrides PlanTemplate value.
    """

    standing_charge_accounting_product_id: Annotated[str, PropertyInfo(alias="standingChargeAccountingProductId")]
    """
    Optional Product ID this plan's standing charge should be attributed to for
    accounting purposes
    """

    standing_charge_bill_in_advance: Annotated[bool, PropertyInfo(alias="standingChargeBillInAdvance")]
    """When TRUE, standing charge is billed at the start of each billing period.

    When FALSE, standing charge is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
    billing in arrears/in advance.
    """

    standing_charge_description: Annotated[str, PropertyInfo(alias="standingChargeDescription")]
    """Standing charge description _(displayed on the bill line item)_."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
