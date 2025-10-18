# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from ..data_explorer_group import DataExplorerGroup

__all__ = ["UsageDataExportScheduleResponse", "Aggregation", "DimensionFilter"]


class Aggregation(BaseModel):
    field_code: str = FieldInfo(alias="fieldCode")
    """Field code"""

    field_type: Literal["DIMENSION", "MEASURE"] = FieldInfo(alias="fieldType")
    """Type of field"""

    function: Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE"]
    """Aggregation function"""

    meter_id: str = FieldInfo(alias="meterId")
    """Meter ID"""


class DimensionFilter(BaseModel):
    field_code: str = FieldInfo(alias="fieldCode")
    """Field code"""

    meter_id: str = FieldInfo(alias="meterId")
    """Meter ID"""

    values: List[str]
    """Values to filter by"""


class UsageDataExportScheduleResponse(BaseModel):
    id: str
    """The id of the schedule configuration."""

    account_ids: Optional[List[str]] = FieldInfo(alias="accountIds", default=None)
    """List of account IDs for which the usage data will be exported."""

    aggregations: Optional[List[Aggregation]] = None
    """List of aggregations to apply"""

    dimension_filters: Optional[List[DimensionFilter]] = FieldInfo(alias="dimensionFilters", default=None)
    """List of dimension filters to apply"""

    groups: Optional[List[DataExplorerGroup]] = None
    """List of groups to apply"""

    meter_ids: Optional[List[str]] = FieldInfo(alias="meterIds", default=None)
    """List of meter IDs for which the usage data will be exported."""

    time_period: Optional[
        Literal[
            "TODAY",
            "YESTERDAY",
            "WEEK_TO_DATE",
            "MONTH_TO_DATE",
            "YEAR_TO_DATE",
            "PREVIOUS_WEEK",
            "PREVIOUS_MONTH",
            "PREVIOUS_QUARTER",
            "PREVIOUS_YEAR",
            "LAST_12_HOURS",
            "LAST_7_DAYS",
            "LAST_30_DAYS",
            "LAST_35_DAYS",
            "LAST_90_DAYS",
            "LAST_120_DAYS",
            "LAST_YEAR",
        ]
    ] = FieldInfo(alias="timePeriod", default=None)
    """
    Define a time period to control the range of usage data you want the data export
    to contain when it runs:

    - **TODAY**. Data collected for the current day up until the time the export is
      scheduled to run.
    - **YESTERDAY**. Data collected for the day before the export runs under the
      schedule - that is, the 24 hour period from midnight to midnight of the day
      before.
    - **PREVIOUS_WEEK**, **PREVIOUS_MONTH**, **PREVIOUS_QUARTER**,
      **PREVIOUS_YEAR**. Data collected for the previous full week, month, quarter,
      or year period. For example if **PREVIOUS_WEEK**, weeks run Monday to Monday -
      if the export is scheduled to run on June 12th 2024, which is a Wednesday, the
      export will contain data for the period running from Monday, June 3rd 2024 to
      midnight on Sunday, June 9th 2024.
    - **WEEK_TO_DATE**, **MONTH_TO_DATE**, or **YEAR_TO_DATE**. Data collected for
      the period covering the current week, month, or year period. For example if
      **WEEK_TO_DATE**, weeks run Monday to Monday - if the Export is scheduled to
      run at 10 a.m. UTC on October 16th 2024, which is a Wednesday, it will contain
      all usage data collected starting Monday October 14th 2024 through to the
      Wednesday at 10 a.m. UTC of the current week.
    - **LAST_12_HOURS**. Data collected for the twelve hour period up to the start
      of the hour in which the export is scheduled to run.
    - **LAST_7_DAYS**, **LAST_30_DAYS**, **LAST_35_DAYS**, **LAST_90_DAYS**,
      **LAST_120_DAYS** **LAST_YEAR**. Data collected for the selected period prior
      to the date the export is scheduled to run. For example if **LAST_30_DAYS**
      and the export is scheduled to run for any time on June 15th 2024, it will
      contain usage data collected for the previous 30 days - starting May 16th 2024
      through to midnight on June 14th 2024

    For more details and examples, see the
    [Time Period](https://www.m3ter.com/docs/guides/data-exports/creating-export-schedules#time-period)
    section in our main User Documentation.
    """

    version: Optional[int] = None
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """
