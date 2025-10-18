# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .data_explorer_group_param import DataExplorerGroupParam

__all__ = ["UsageQueryParams", "Aggregation", "DimensionFilter"]


class UsageQueryParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountIds")]
    """Specify the Accounts you want the query to return usage data for."""

    aggregations: Iterable[Aggregation]
    """
    Define the Aggregation functions you want to apply to data fields on included
    Meters:

    - **SUM**. Adds the values.
    - **MIN**. Uses the minimum value.
    - **MAX**. Uses the maximum value.
    - **COUNT**. Counts the number of values.
    - **LATEST**. Uses the most recent value.
    - **MEAN**. Uses the arithmetic mean of the values.
    - **UNIQUE**. Uses a count of the number of unique values.

    **NOTE!** The Aggregation functions that can be applied depend on the data field
    type:

    - **Measure** fields. `SUM`, `MIN`, `MAX`, `COUNT`, `LATEST`, or `MEAN`
      functions can be applied.
    - **Dimension** field. `COUNT` or `UNIQUE` functions can be applied.
    """

    dimension_filters: Annotated[Iterable[DimensionFilter], PropertyInfo(alias="dimensionFilters")]
    """Define Dimension filters you want to apply for the query.

    Specify values for Dimension data fields on included Meters. Only data that
    match the specified Dimension field values will be returned for the query.
    """

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """The exclusive end date to define a time period to filter by.

    (_ISO 8601 formatted_)
    """

    groups: Iterable[DataExplorerGroupParam]
    """
    If you've applied Aggregations for your query, specify any grouping you want to
    impose on the returned data:

    - **Account**
    - **Time** - group by frequency. Five options: `DAY`, `HOUR`, `WEEK`, `MONTH`,
      or `QUARTER`.
    - **Dimension** - group by Meter and data field.

    **NOTE:** If you attempt to impose grouping for a query that doesn't apply
    Aggregations, you'll receive an error.
    """

    limit: int
    """
    Define a limit for the number of usage data items you want the query to return,
    starting with the most recently received data item.
    """

    meter_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="meterIds")]
    """Specify the Meters you want the query to return usage data for."""

    start_date: Annotated[Union[str, datetime], PropertyInfo(alias="startDate", format="iso8601")]
    """The inclusive start date to define a time period to filter by.

    (_ISO 8601 formatted_)
    """


class Aggregation(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    field_type: Required[Annotated[Literal["DIMENSION", "MEASURE"], PropertyInfo(alias="fieldType")]]
    """Type of field"""

    function: Required[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE"]]
    """Aggregation function"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""


class DimensionFilter(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""

    values: Required[SequenceNotStr[str]]
    """Values to filter by"""
