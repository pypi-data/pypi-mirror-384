# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from datetime import date, datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AccountPlanCreateParams"]


class AccountPlanCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """The unique identifier (UUID) for the Account."""

    start_date: Required[Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]]
    """
    The start date _(in ISO-8601 format)_ for the AccountPlan or AccountPlanGroup
    becoming active for the Account.
    """

    bill_epoch: Annotated[Union[str, date], PropertyInfo(alias="billEpoch", format="iso8601")]
    """
    Optional setting to define a _billing cycle date_, which acts as a reference for
    when in the applied billing frequency period bills are created:

    - For example, if you attach a Plan to an Account where the Plan is configured
      for monthly billing frequency and you've defined the period the Plan will
      apply to the Account to be from January 1st, 2022 until January 1st, 2023. You
      then set a `billEpoch` date of February 15th, 2022. The first Bill will be
      created for the Account on February 15th, and subsequent Bills created on the
      15th of the months following for the remainder of the billing period - March
      15th, April 15th, and so on.
    - If not defined, then the `billEpoch` date set for the Account will be used
      instead.
    - The date is in ISO-8601 format.
    """

    child_billing_mode: Annotated[
        Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"], PropertyInfo(alias="childBillingMode")
    ]
    """
    If the Account is either a Parent or a Child Account, this specifies the Account
    hierarchy billing mode. The mode determines how billing will be handled and
    shown on bills for charges due on the Parent Account, and charges due on Child
    Accounts:

    - **Parent Breakdown** - a separate bill line item per Account. Default setting.

    - **Parent Summary** - single bill line item for all Accounts.

    - **Child** - the Child Account is billed.
    """

    code: str
    """A unique short code for the AccountPlan or AccountPlanGroup."""

    contract_id: Annotated[str, PropertyInfo(alias="contractId")]
    """
    The unique identifier (UUID) for a Contract to which you want to add the Plan or
    Plan Group being attached to the Account.
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

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """
    The end date _(in ISO-8601 format)_ for when the AccountPlan or AccountPlanGroup
    ceases to be active for the Account. If not specified, the AccountPlan or
    AccountPlanGroup remains active indefinitely.
    """

    plan_group_id: Annotated[str, PropertyInfo(alias="planGroupId")]
    """
    The unique identifier (UUID) of the PlanGroup to be attached to the Account to
    create an AccountPlanGroup.

    **Note:** Exclusive of the `planId` request parameter - exactly one of `planId`
    or `planGroupId` must be used per call.
    """

    plan_id: Annotated[str, PropertyInfo(alias="planId")]
    """
    The unique identifier (UUID) of the Plan to be attached to the Account to create
    an AccountPlan.

    **Note:** Exclusive of the `planGroupId` request parameter - exactly one of
    `planId` or `planGroupId` must be used per call.
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
