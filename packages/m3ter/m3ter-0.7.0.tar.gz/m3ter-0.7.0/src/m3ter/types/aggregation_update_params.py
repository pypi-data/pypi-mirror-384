# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["AggregationUpdateParams"]


class AggregationUpdateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    aggregation: Required[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"]]
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

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """The UUID of the Meter used as the source of usage data for the Aggregation.

    Each Aggregation is a child of a Meter, so the Meter must be selected.
    """

    name: Required[str]
    """Descriptive name for the Aggregation."""

    quantity_per_unit: Required[Annotated[float, PropertyInfo(alias="quantityPerUnit")]]
    """Defines how much of a quantity equates to 1 unit.

    Used when setting the price per unit for billing purposes - if charging for
    kilobytes per second (KiBy/s) at rate of $0.25 per 500 KiBy/s, then set
    quantityPerUnit to 500 and price Plan at $0.25 per unit.

    **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
    typically set to `"UP"`.
    """

    rounding: Required[Literal["UP", "DOWN", "NEAREST", "NONE"]]
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

    target_field: Required[Annotated[str, PropertyInfo(alias="targetField")]]
    """
    `Code` of the target `dataField` or `derivedField` on the Meter used as the
    basis for the Aggregation.
    """

    unit: Required[str]
    """
    User defined label for units shown for Bill line items, indicating to your
    customers what they are being charged for.
    """

    accounting_product_id: Annotated[str, PropertyInfo(alias="accountingProductId")]
    """
    Optional Product ID this Aggregation should be attributed to for accounting
    purposes
    """

    code: str
    """Code of the new Aggregation. A unique short code to identify the Aggregation."""

    custom_fields: Annotated[Dict[str, Union[str, float]], PropertyInfo(alias="customFields")]

    custom_sql: Annotated[str, PropertyInfo(alias="customSql")]
    """
    **NOTE:** The `customSql` Aggregation type is currently only available in Beta
    release and on request. If you are interested in using this feature, please get
    in touch with m3ter Support or your m3ter contact.
    """

    default_value: Annotated[float, PropertyInfo(alias="defaultValue")]
    """Aggregation value used when no usage data is available to be aggregated.

    _(Optional)_.

    **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
    Aggregation. This ensures that any null values are passed in correctly to the
    Compound Aggregation calculation with a value = 0.
    """

    segmented_fields: Annotated[SequenceNotStr[str], PropertyInfo(alias="segmentedFields")]
    """_(Optional)_.

    Used when creating a segmented Aggregation, which segments the usage data
    collected by a single Meter. Works together with `segments`.

    Enter the `Codes` of the fields in the target Meter to use for segmentation
    purposes.

    String `dataFields` on the target Meter can be segmented. Any string
    `derivedFields` on the target Meter, such as one that concatenates two string
    `dataFields`, can also be segmented.
    """

    segments: Iterable[Dict[str, str]]
    """_(Optional)_.

    Used when creating a segmented Aggregation, which segments the usage data
    collected by a single Meter. Works together with `segmentedFields`.

    Enter the values that are to be used as the segments, read from the fields in
    the meter pointed at by `segmentedFields`.

    Note that you can use _wildcards_ or _defaults_ when setting up segment values.
    For more details on how to do this with an example, see
    [Using Wildcards - API Calls](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/segmented-aggregations#using-wildcards---api-calls)
    in our main User Docs.
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
