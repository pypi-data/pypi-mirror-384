# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CompoundAggregationResponse"]


class CompoundAggregationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)

    calculation: Optional[str] = None
    """This field is a string that represents the formula for the calculation.

    This formula determines how the CompoundAggregation is calculated from the
    underlying usage data.
    """

    code: Optional[str] = None
    """Code of the Aggregation. A unique short code to identify the Aggregation."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The unique identifier (UUID) of the user who created this CompoundAggregation."""

    custom_fields: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="customFields", default=None)

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the CompoundAggregation was
    created.
    """

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """
    The date and time _(in ISO-8601 format)_ when the CompoundAggregation was last
    modified.
    """

    evaluate_null_aggregations: Optional[bool] = FieldInfo(alias="evaluateNullAggregations", default=None)
    """This is a boolean True / False flag.

    If set to TRUE, the calculation will be evaluated even if the referenced
    aggregation has no usage data.
    """

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """
    The unique identifier (UUID) of the user who last modified this
    CompoundAggregation.
    """

    name: Optional[str] = None
    """Descriptive name for the Aggregation."""

    product_id: Optional[str] = FieldInfo(alias="productId", default=None)
    """
    This field represents the unique identifier (UUID) of the Product that is
    associated with the CompoundAggregation.
    """

    quantity_per_unit: Optional[float] = FieldInfo(alias="quantityPerUnit", default=None)
    """Defines how much of a quantity equates to 1 unit.

    Used when setting the price per unit for billing purposes - if charging for
    kilobytes per second (KiBy/s) at rate of $0.25 per 500 KiBy/s, then set
    quantityPerUnit to 500 and price Plan at $0.25 per unit.

    If `quantityPerUnit` is set to a value other than one, rounding is typically set
    to UP.
    """

    rounding: Optional[Literal["UP", "DOWN", "NEAREST", "NONE"]] = None
    """
    Specifies how you want to deal with non-integer, fractional number Aggregation
    values.

    **NOTES:**

    - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
      rounded to 4.
    - Also used in combination with `quantityPerUnit`. Rounds the number of units
      after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
      other than one, you would typically set Rounding to **UP**. For example,
      suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
      500, and set charge rate at $0.25 per unit used. If your customer used 48,900
      KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
      to 98 \\** 0.25 = $2.45.

    Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???
    """

    segments: Optional[List[Dict[str, str]]] = None
    """_(Optional)_.

    Used when creating a segmented Aggregation, which segments the usage data
    collected by a single Meter. Works together with `segmentedFields`.

    Contains the values that are to be used as the segments, read from the fields in
    the meter pointed at by `segmentedFields`.
    """

    unit: Optional[str] = None
    """User defined or following the _Unified Code for Units of Measure_ (UCUM).

    Used as the label for billing, indicating to your customers what they are being
    charged for.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
