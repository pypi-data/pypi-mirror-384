# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Balance"]


class Balance(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """
    The unique identifier (UUID) for the end customer Account the Balance belongs
    to.
    """

    amount: Optional[float] = None
    """The financial value that the Balance holds."""

    balance_draw_down_description: Optional[str] = FieldInfo(alias="balanceDrawDownDescription", default=None)
    """
    A description for the bill line items for charges drawn-down against the
    Balance.
    """

    code: Optional[str] = None
    """A unique short code assigned to the Balance."""

    consumptions_accounting_product_id: Optional[str] = FieldInfo(alias="consumptionsAccountingProductId", default=None)

    contract_id: Optional[str] = FieldInfo(alias="contractId", default=None)

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) for the user who created the Balance."""

    currency: Optional[str] = None
    """The currency code used for the Balance amount. For example: USD, GBP or EUR."""

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

    description: Optional[str] = None
    """A description of the Balance."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO 8601 format)_ when the Balance was first created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO 8601 format)_ when the Balance was last modified."""

    end_date: Optional[datetime] = FieldInfo(alias="endDate", default=None)
    """
    The date _(in ISO 8601 format)_ after which the Balance will no longer be
    active.
    """

    fees_accounting_product_id: Optional[str] = FieldInfo(alias="feesAccountingProductId", default=None)

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) for the user who last modified the Balance."""

    line_item_types: Optional[
        List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ]
    ] = FieldInfo(alias="lineItemTypes", default=None)
    """
    A list of line item charge types that can draw-down against the Balance amount
    at billing.
    """

    name: Optional[str] = None
    """The official name of the Balance."""

    overage_description: Optional[str] = FieldInfo(alias="overageDescription", default=None)
    """A description for overage charges."""

    overage_surcharge_percent: Optional[float] = FieldInfo(alias="overageSurchargePercent", default=None)
    """
    The percentage surcharge applied to overage charges _(usage above the Balance)_.
    """

    product_ids: Optional[List[str]] = FieldInfo(alias="productIds", default=None)
    """
    A list of Product IDs whose consumption charges due at billing can be drawn-down
    against the Balance amount.
    """

    rollover_amount: Optional[float] = FieldInfo(alias="rolloverAmount", default=None)
    """
    The maximum amount that can be carried over past the Balance end date and
    draw-down against for billing if there is an unused Balance amount remaining
    when the Balance end date is reached.
    """

    rollover_end_date: Optional[datetime] = FieldInfo(alias="rolloverEndDate", default=None)
    """
    The end date _(in ISO 8601 format)_ for the rollover grace period, which is the
    period that unused Balance amounts can be carried over beyond the specified
    Balance `endDate` and continue to be drawn-down against for billing.
    """

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """The date _(in ISO 8601 format)_ when the Balance becomes active."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
