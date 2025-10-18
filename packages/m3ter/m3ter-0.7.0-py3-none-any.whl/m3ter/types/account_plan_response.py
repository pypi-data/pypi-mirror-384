# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AccountPlanResponse"]


class AccountPlanResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """
    The unique identifier (UUID) for the Account to which the AccountPlan or
    AccounPlanGroup is attached.
    """

    bill_epoch: Optional[date] = FieldInfo(alias="billEpoch", default=None)
    """
    The initial date for creating the first bill against the Account for charges due
    under the AccountPlan or AccountPlanGroup. All subsequent bill creation dates
    are calculated from this date. If left empty, the first bill date definedfor the
    Account is used. The date is in ISO-8601 format.
    """

    child_billing_mode: Optional[Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"]] = FieldInfo(
        alias="childBillingMode", default=None
    )
    """
    If the Account is either a Parent or a Child Account, this specifies the Account
    hierarchy billing mode. The mode determines how billing will be handled and
    shown on bills for charges due on the Parent Account, and charges due on Child
    Accounts:

    - **Parent Breakdown** - a separate bill line item per Account. Default setting.

    - **Parent Summary** - single bill line item for all Accounts.

    - **Child** - the Child Account is billed.
    """

    code: Optional[str] = None
    """The unique short code of the AccountPlan or AccountPlanGroup."""

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)
    """
    The unique identifier (UUID) for the Contract to which the Plan or Plan Group
    attached to the Account has been added.
    """

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """
    The unique identifier (UUID) for the user who created the AccountPlan or
    AccountPlanGroup.
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
    """
    The date and time _(in ISO 8601 format)_ when the AccountPlan or
    AccountPlanGroup was first created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO 8601 format)_ when the AccountPlan or
    AccountPlanGroup was last modified.
    """

    end_date: Optional[datetime] = FieldInfo(alias="endDate", default=None)
    """
    The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
    ceases to be active for the Account. If not specified, the AccountPlan or
    AccountPlanGroup remains active indefinitely.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) for the user who last modified the AccountPlan or
    AccountPlanGroup.
    """

    plan_group_id: Optional[str] = FieldInfo(alias="planGroupId", default=None)
    """
    The unique identifier (UUID) of the Plan Group that has been attached to the
    Account to create the AccountPlanGroup.
    """

    plan_id: Optional[str] = FieldInfo(alias="planId", default=None)
    """
    The unique identifier (UUID) of the Plan that has been attached to the Account
    to create the AccountPlan.
    """

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """The unique identifier (UUID) for the Product associated with the AccountPlan.

    **Note:** Not present in response for AccountPlanGroup - Plan Groups can contain
    multiple Plans belonging to different Products.
    """

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """
    The start date _(in ISO-8601 format)_ for the when the AccountPlan or
    AccountPlanGroup starts to be active for the Account.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
