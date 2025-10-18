# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .data_explorer_group_param import DataExplorerGroupParam

__all__ = ["AdHocUsageDataRequestParam", "Aggregation", "DimensionFilter"]


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


class AdHocUsageDataRequestParam(TypedDict, total=False):
    source_type: Required[Annotated[Literal["USAGE"], PropertyInfo(alias="sourceType")]]
    """The type of data to export. Possible values are: USAGE"""

    account_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountIds")]
    """List of account IDs for which the usage data will be exported."""

    aggregations: Iterable[Aggregation]
    """List of aggregations to apply"""

    dimension_filters: Annotated[Iterable[DimensionFilter], PropertyInfo(alias="dimensionFilters")]
    """List of dimension filters to apply"""

    end_date: Annotated[Union[str, datetime], PropertyInfo(alias="endDate", format="iso8601")]
    """The exclusive end date for the data export."""

    groups: Iterable[DataExplorerGroupParam]
    """List of groups to apply"""

    meter_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="meterIds")]
    """List of meter IDs for which the usage data will be exported."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
