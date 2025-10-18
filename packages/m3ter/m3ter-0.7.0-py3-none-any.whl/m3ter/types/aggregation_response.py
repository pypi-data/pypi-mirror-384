# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AggregationResponse"]


class AggregationResponse(BaseModel):
    id: str
    """The UUID of the entity."""

    accounting_product_id: Optional[str] = FieldInfo(alias="accountingProductId", default=None)

    aggregation: Optional[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"]] = None
    """
    Specifies the computation method applied to usage data collected in
    `targetField`. Aggregation unit value depends on the **Category** configured for
    the selected targetField.

    Enum:

    - **SUM**. Adds the values. Can be applied to a **Measure**, **Income**, or
      **Cost** `targetField`.

    - **MIN**. Uses the minimum value. Can be applied to a **Measure**, **Income**,
      or **Cost** `targetField`.

    - **MAX**. Uses the maximum value. Can be applied to a **Measure**, **Income**,
      or **Cost** `targetField`.

    - **COUNT**. Counts the number of values. Can be applied to a **Measure**,
      **Income**, or **Cost** `targetField`.

    - **LATEST**. Uses the most recent value. Can be applied to a **Measure**,
      **Income**, or **Cost** `targetField`. Note: Based on the timestamp (`ts`)
      value of usage data measurement submissions. If using this method, please
      ensure _distinct_ `ts` values are used for usage data measurment submissions.

    - **MEAN**. Uses the arithmetic mean of the values. Can be applied to a
      **Measure**, **Income**, or **Cost** `targetField`.

    - **UNIQUE**. Uses unique values and returns a count of the number of unique
      values. Can be applied to a **Metadata** `targetField`.
    """

    code: Optional[str] = None
    """Code of the Aggregation. A unique short code to identify the Aggregation."""

    created_by: Optional[str] = FieldInfo(alias="createdBy", default=None)
    """The id of the user who created this aggregation."""

    custom_fields: Optional[Dict[str, Union[str, float]]] = FieldInfo(alias="customFields", default=None)

    custom_sql: Optional[str] = FieldInfo(alias="customSql", default=None)

    default_value: Optional[float] = FieldInfo(alias="defaultValue", default=None)
    """Aggregation value used when no usage data is available to be aggregated.

    _(Optional)_.

    **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
    Aggregation. This ensures that any null values are passed in correctly to the
    Compound Aggregation calculation with a value = 0.
    """

    dt_created: Optional[datetime] = FieldInfo(alias="dtCreated", default=None)
    """The DateTime when the aggregation was created _(in ISO 8601 format)_."""

    dt_last_modified: Optional[datetime] = FieldInfo(alias="dtLastModified", default=None)
    """The DateTime when the aggregation was last modified _(in ISO 8601 format)_."""

    last_modified_by: Optional[str] = FieldInfo(alias="lastModifiedBy", default=None)
    """The id of the user who last modified this aggregation."""

    meter_id: Optional[str] = FieldInfo(alias="meterId", default=None)
    """The UUID of the Meter used as the source of usage data for the Aggregation.

    Each Aggregation is a child of a Meter, so the Meter must be selected.
    """

    name: Optional[str] = None
    """Descriptive name for the Aggregation."""

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

    segmented_fields: Optional[List[str]] = FieldInfo(alias="segmentedFields", default=None)
    """_(Optional)_.

    Used when creating a segmented Aggregation, which segments the usage data
    collected by a single Meter. Works together with `segments`.

    The `Codes` of the fields in the target Meter to use for segmentation purposes.

    String `dataFields` on the target Meter can be segmented. Any string
    `derivedFields` on the target Meter, such as one that concatenates two string
    `dataFields`, can also be segmented.
    """

    segments: Optional[List[Dict[str, str]]] = None
    """_(Optional)_.

    Used when creating a segmented Aggregation, which segments the usage data
    collected by a single Meter. Works together with `segmentedFields`.

    Contains the values that are to be used as the segments, read from the fields in
    the meter pointed at by `segmentedFields`.
    """

    target_field: Optional[str] = FieldInfo(alias="targetField", default=None)
    """
    `Code` of the target `dataField` or `derivedField` on the Meter used as the
    basis for the Aggregation.
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
