# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PlanGroupResponse"]


class PlanGroupResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """Optional.

    This PlanGroup was created as bespoke for the associated Account with this
    Account ID.
    """

    code: Optional[str] = None
    """The short code representing the PlanGroup."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the PlanGroup."""

    currency: Optional[str] = None
    """Currency code for the PlanGroup (For example, USD)."""

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
    """The date and time _(in ISO 8601 format)_ when the PlanGroup was first created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO 8601 format)_ when the PlanGroup was last modified."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) for the user who last modified the PlanGroup."""

    minimum_spend: Optional[float] = FieldInfo(alias="minimumSpend", default=None)
    """The minimum spend amount for the PlanGroup."""

    minimum_spend_accounting_product_id: Optional[str] = FieldInfo(
        alias="minimumSpendAccountingProductId", default=None
    )
    """Optional.

    Product ID to attribute the PlanGroup's minimum spend for accounting purposes.
    """

    minimum_spend_bill_in_advance: Optional[bool] = FieldInfo(alias="minimumSpendBillInAdvance", default=None)
    """A boolean flag that determines when the minimum spend is billed.

    This flag overrides the setting at Organizational level for minimum spend
    billing in arrears/in advance.

    - **TRUE** - minimum spend is billed at the start of each billing period.
    - **FALSE** - minimum spend is billed at the end of each billing period.
    """

    minimum_spend_description: Optional[str] = FieldInfo(alias="minimumSpendDescription", default=None)
    """Description of the minimum spend, displayed on the bill line item."""

    name: Optional[str] = None
    """The name of the PlanGroup."""

    standing_charge: Optional[float] = FieldInfo(alias="standingCharge", default=None)
    """Standing charge amount for the PlanGroup."""

    standing_charge_accounting_product_id: Optional[str] = FieldInfo(
        alias="standingChargeAccountingProductId", default=None
    )
    """Optional.

    Product ID to attribute the PlanGroup's standing charge for accounting purposes.
    """

    standing_charge_bill_in_advance: Optional[bool] = FieldInfo(alias="standingChargeBillInAdvance", default=None)
    """A boolean flag that determines when the standing charge is billed.

    This flag overrides the setting at Organizational level for standing charge
    billing in arrears/in advance.

    - **TRUE** - standing charge is billed at the start of each billing period.
    - **FALSE** - standing charge is billed at the end of each billing period.
    """

    standing_charge_description: Optional[str] = FieldInfo(alias="standingChargeDescription", default=None)
    """Description of the standing charge, displayed on the bill line item."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
