# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import date, datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["ContractResponse"]


class ContractResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account_id: Optional[str] = FieldInfo(alias="accountId", default=None)
    """The unique identifier (UUID) of the Account associated with this Contract."""

    bill_grouping_key: Optional[str] = FieldInfo(alias="billGroupingKey", default=None)

    code: Optional[str] = None
    """The short code of the Contract."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this Contract."""

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
    """The description of the Contract, which provides context and information."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The date and time _(in ISO-8601 format)_ when the Contract was created."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The date and time _(in ISO-8601 format)_ when the Contract was last modified."""

    end_date: Optional[date] = FieldInfo(alias="endDate", default=None)
    """The exclusive end date of the Contract _(in ISO-8601 format)_.

    This means the Contract is active until midnight on the day **_before_** this
    date.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The unique identifier (UUID) of the user who last modified this Contract."""

    name: Optional[str] = None
    """The name of the Contract."""

    purchase_order_number: Optional[str] = FieldInfo(alias="purchaseOrderNumber", default=None)
    """The Purchase Order Number associated with the Contract."""

    start_date: Optional[date] = FieldInfo(alias="startDate", default=None)
    """The start date for the Contract _(in ISO-8601 format)_.

    This date is inclusive, meaning the Contract is active from this date onward.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
