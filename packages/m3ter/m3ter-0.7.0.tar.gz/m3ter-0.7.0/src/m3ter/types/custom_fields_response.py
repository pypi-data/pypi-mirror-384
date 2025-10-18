# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CustomFieldsResponse"]


class CustomFieldsResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    account: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to Account entities."""

    account_plan: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="accountPlan", default=None)
    """CustomFields added to accountPlan entities."""

    aggregation: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to simple Aggregation entities."""

    compound_aggregation: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="compoundAggregation", default=None)
    """CustomFields added to Compound Aggregation entities."""

    contract: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to Contract entities."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this custom field."""

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the Organization was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The DateTime when a custom field was last modified - created, modified, or
    deleted - for the Organization _(in ISO-8601 format)_.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this custom field."""

    meter: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to Meter entities."""

    organization: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to the Organization."""

    plan: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to Plan entities."""

    plan_template: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="planTemplate", default=None)
    """CustomFields added to planTemplate entities."""

    product: Optional[Dict[str, Union[str, float]]] = None
    """CustomFields added to Product entities."""

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
