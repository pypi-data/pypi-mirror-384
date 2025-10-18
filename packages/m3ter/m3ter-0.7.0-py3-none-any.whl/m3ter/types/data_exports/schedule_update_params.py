# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo
from ..data_explorer_group_param import DataExplorerGroupParam

__all__ = [
    "ScheduleUpdateParams",
    "OperationalDataExportScheduleRequest",
    "UsageDataExportScheduleRequest",
    "UsageDataExportScheduleRequestAggregation",
    "UsageDataExportScheduleRequestDimensionFilter",
]


class OperationalDataExportScheduleRequest(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    operational_data_types: Required[
        Annotated[
            List[
                Literal[
                    "BILLS",
                    "COMMITMENTS",
                    "ACCOUNTS",
                    "BALANCES",
                    "CONTRACTS",
                    "ACCOUNT_PLANS",
                    "AGGREGATIONS",
                    "PLANS",
                    "PRICING",
                    "PRICING_BANDS",
                    "BILL_LINE_ITEMS",
                    "METERS",
                    "PRODUCTS",
                    "COMPOUND_AGGREGATIONS",
                    "PLAN_GROUPS",
                    "PLAN_GROUP_LINKS",
                    "PLAN_TEMPLATES",
                    "BALANCE_TRANSACTIONS",
                    "TRANSACTION_TYPES",
                ]
            ],
            PropertyInfo(alias="operationalDataTypes"),
        ]
    ]
    """A list of the entities whose operational data is included in the data export."""

    source_type: Required[Annotated[Literal["OPERATIONAL"], PropertyInfo(alias="sourceType")]]
    """The type of data to export. Possible values are: OPERATIONAL"""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class UsageDataExportScheduleRequest(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    source_type: Required[Annotated[Literal["USAGE"], PropertyInfo(alias="sourceType")]]
    """The type of data to export. Possible values are: USAGE"""

    time_period: Required[
        Annotated[
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
            ],
            PropertyInfo(alias="timePeriod"),
        ]
    ]
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

    account_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountIds")]
    """List of account IDs to export"""

    aggregations: Iterable[UsageDataExportScheduleRequestAggregation]
    """List of aggregations to apply"""

    dimension_filters: Annotated[
        Iterable[UsageDataExportScheduleRequestDimensionFilter], PropertyInfo(alias="dimensionFilters")
    ]
    """List of dimension filters to apply"""

    groups: Iterable[DataExplorerGroupParam]
    """List of groups to apply"""

    meter_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="meterIds")]
    """List of meter IDs to export"""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class UsageDataExportScheduleRequestAggregation(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    field_type: Required[Annotated[Literal["DIMENSION", "MEASURE"], PropertyInfo(alias="fieldType")]]
    """Type of field"""

    function: Required[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE"]]
    """Aggregation function"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""


class UsageDataExportScheduleRequestDimensionFilter(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""

    values: Required[SequenceNotStr[str]]
    """Values to filter by"""


ScheduleUpdateParams: TypeAlias = Union[OperationalDataExportScheduleRequest, UsageDataExportScheduleRequest]
