# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel
from .data_field import DataField
from .derived_field import DerivedField

__all__ = ["MeterResponse"]


class MeterResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    code: Optional[str] = None
    """Code of the Meter - unique short code used to identify the Meter."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this meter."""

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

    data_fields: Optional[List[DataField]] = FieldInfo(alias="dataFields", default=None)
    """
    Used to submit categorized raw usage data values for ingest into the platform -
    either numeric quantitative values or non-numeric data values. At least one
    required per Meter; maximum 15 per Meter.
    """

    derived_fields: Optional[List[DerivedField]] = FieldInfo(alias="derivedFields", default=None)
    """
    Used to submit usage data values for ingest into the platform that are the
    result of a calculation performed on `dataFields`, `customFields`, or system
    `Timestamp` fields. Raw usage data is not submitted using `derivedFields`.
    Maximum 15 per Meter. _(Optional)_.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the meter was created _(in ISO-8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the meter was last modified _(in ISO-8601 format)_."""

    group_id: Optional[str] = FieldInfo(alias="groupId", default=None)
    """UUID of the MeterGroup the Meter belongs to. _(Optional)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this meter."""

    name: Optional[str] = None
    """Descriptive name for the Meter."""

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """UUID of the Product the Meter belongs to.

    _(Optional)_ - if blank, the Meter is global.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
