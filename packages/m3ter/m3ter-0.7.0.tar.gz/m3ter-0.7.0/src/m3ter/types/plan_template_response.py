# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["PlanTemplateResponse"]


class PlanTemplateResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    bill_frequency: Optional[Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"]] = FieldInfo(
        alias="billFrequency", default=None
    )
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

    bill_frequency_interval: Optional[int] = FieldInfo(alias="billFrequencyInterval", default=None)
    """How often bills are issued.

    For example, if `billFrequency` is Monthly and `billFrequencyInterval` is 3,
    bills are issued every three months.
    """

    code: Optional[str] = None
    """A unique, short code reference for the PlanTemplate.

    This code should not contain control characters or spaces.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this PlanTemplate."""

    currency: Optional[str] = None
    """
    The ISO currency code for the pricing currency used by Plans based on the Plan
    Template to define charge rates for Product consumption - for example USD, GBP,
    EUR.
    """

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
    """The date and time _(in ISO-8601 format)_ when the PlanTemplate was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the PlanTemplate was last
    modified.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this PlanTemplate."""

    minimum_spend: Optional[float] = FieldInfo(alias="minimumSpend", default=None)
    """
    The Product minimum spend amount per billing cycle for end customer Accounts on
    a pricing Plan based on the PlanTemplate. This must be a non-negative number.
    """

    minimum_spend_bill_in_advance: Optional[bool] = FieldInfo(alias="minimumSpendBillInAdvance", default=None)
    """A boolean that determines when the minimum spend is billed.

    - TRUE - minimum spend is billed at the start of each billing period.
    - FALSE - minimum spend is billed at the end of each billing period.

    Overrides the setting at Organizational level for minimum spend billing in
    arrears/in advance.
    """

    minimum_spend_description: Optional[str] = FieldInfo(alias="minimumSpendDescription", default=None)
    """Minimum spend description _(displayed on the bill line item)_."""

    name: Optional[str] = None
    """Descriptive name for the PlanTemplate."""

    ordinal: Optional[int] = None
    """The ranking of the PlanTemplate among your pricing plans.

    Lower numbers represent more basic plans, while higher numbers represent premium
    plans. This must be a non-negative integer.

    **NOTE:** **DEPRECATED** - no longer used.
    """

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """The unique identifier (UUID) of the Product associated with this PlanTemplate."""

    standing_charge: Optional[float] = FieldInfo(alias="standingCharge", default=None)
    """The fixed charge _(standing charge)_ applied to customer bills.

    This charge is prorated and must be a non-negative number.
    """

    standing_charge_bill_in_advance: Optional[bool] = FieldInfo(alias="standingChargeBillInAdvance", default=None)
    """A boolean that determines when the standing charge is billed.

    - TRUE - standing charge is billed at the start of each billing period.
    - FALSE - standing charge is billed at the end of each billing period.

    Overrides the setting at Organizational level for standing charge billing in
    arrears/in advance.
    """

    standing_charge_description: Optional[str] = FieldInfo(alias="standingChargeDescription", default=None)
    """Standing charge description _(displayed on the bill line item)_."""

    standing_charge_interval: Optional[int] = FieldInfo(alias="standingChargeInterval", default=None)
    """How often the standing charge is applied.

    For example, if the bill is issued every three months and
    `standingChargeInterval` is 2, then the standing charge is applied every six
    months.
    """

    standing_charge_offset: Optional[int] = FieldInfo(alias="standingChargeOffset", default=None)
    """Defines an offset for when the standing charge is first applied.

    For example, if the bill is issued every three months and the
    `standingChargeOfset` is 0, then the charge is applied to the first bill _(at
    three months)_; if 1, it would be applied to the second bill _(at six months)_,
    and so on.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
