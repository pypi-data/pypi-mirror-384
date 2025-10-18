# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CounterAdjustmentUpdateParams"]


class CounterAdjustmentUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Required[Annotated[str, PropertyInfo(alias="accountId")]]
    """The Account ID the CounterAdjustment is created for."""

    counter_id: Required[Annotated[str, PropertyInfo(alias="counterId")]]
    """The ID of the Counter used for the CounterAdjustment on the Account."""

    date: Required[str]
    """
    The date the CounterAdjustment is created for the Account _(in ISO-8601 date
    format)_.

    **Note:** CounterAdjustments on Accounts are supported down to a _specific day_
    of granularity - you cannot create more than one CounterAdjustment for any given
    day using the same Counter and you'll receive an error if you try to do this.
    """

    value: Required[int]
    """Integer Value of the Counter used for the CounterAdjustment.

    **Note:** Use the new absolute value for the Counter for the selected date - if
    it was 15 and has increased to 20, enter 20; if it was 15 and has decreased to
    10, enter 10. _Do not enter_ the plus or minus value relative to the previous
    Counter value on the Account.
    """

    purchase_order_number: Annotated[str, PropertyInfo(alias="purchaseOrderNumber")]
    """Purchase Order Number for the Counter Adjustment. _(Optional)_"""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
