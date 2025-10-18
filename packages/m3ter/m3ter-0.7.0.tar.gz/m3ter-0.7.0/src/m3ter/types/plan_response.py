# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PlanResponse"]


class PlanResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """_(Optional)_.

    The Account ID for which this plan was created as custom/bespoke. A
    custom/bespoke Plan can only be attached to the specified Account.
    """

    bespoke: Optional[bool] = None
    """
    TRUE/FALSE flag indicating whether the plan is custom/bespoke for a particular
    Account.
    """

    code: Optional[str] = None
    """Unique short code reference for the Plan."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this plan."""

    custom_fields: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="customFields", default=None)
    """User defined fields enabling you to attach custom data.

    The value for a custom field can be either a string or a number.

    If `customFields` can also be defined for this entity at the Organizational
    level,`customField` values defined at individual level override values of
    `customFields` with the same name defined at Organization level.

    See
    [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
    in the m3ter documentation for more information.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime _(in ISO-8601 format)_ when the plan was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime _(in ISO-8601 format)_ when the plan was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this plan."""

    minimum_spend: Optional[float] = FieldInfo(alias="minimumSpend", default=None)
    """
    The product minimum spend amount per billing cycle for end customer Accounts on
    a priced Plan.

    _(Optional)_. Overrides PlanTemplate value.
    """

    minimum_spend_accounting_product_id: Optional[str] = FieldInfo(
        alias="minimumSpendAccountingProductId", default=None
    )
    """
    Optional Product ID this plan's minimum spend should be attributed to for
    accounting purposes
    """

    minimum_spend_bill_in_advance: Optional[bool] = FieldInfo(alias="minimumSpendBillInAdvance", default=None)
    """When TRUE, minimum spend is billed at the start of each billing period.

    When FALSE, minimum spend is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
    billing in arrears/in advance.
    """

    minimum_spend_description: Optional[str] = FieldInfo(alias="minimumSpendDescription", default=None)
    """Minimum spend description _(displayed on the bill line item)_."""

    name: Optional[str] = None
    """Descriptive name for the Plan."""

    ordinal: Optional[int] = None
    """
    Assigns a rank or position to the Plan in your order of pricing plans - lower
    numbers represent more basic pricing plans; higher numbers represent more
    premium pricing plans.

    _(Optional)_. Overrides PlanTemplate value.

    **NOTE:** **DEPRECATED** - no longer used.
    """

    plan_template_id: Optional[str] = FieldInfo(alias="planTemplateId", default=None)
    """UUID of the PlanTemplate the Plan belongs to."""

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """UUID of the Product the Plan belongs to."""

    standing_charge: Optional[float] = FieldInfo(alias="standingCharge", default=None)
    """The standing charge applied to bills for end customers. This is prorated.

    _(Optional)_. Overrides PlanTemplate value.
    """

    standing_charge_accounting_product_id: Optional[str] = FieldInfo(
        alias="standingChargeAccountingProductId", default=None
    )
    """
    Optional Product ID this plan's standing charge should be attributed to for
    accounting purposes
    """

    standing_charge_bill_in_advance: Optional[bool] = FieldInfo(alias="standingChargeBillInAdvance", default=None)
    """When TRUE, standing charge is billed at the start of each billing period.

    When FALSE, standing charge is billed at the end of each billing period.

    _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
    billing in arrears/in advance.
    """

    standing_charge_description: Optional[str] = FieldInfo(alias="standingChargeDescription", default=None)
    """Standing charge description _(displayed on the bill line item)_."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
