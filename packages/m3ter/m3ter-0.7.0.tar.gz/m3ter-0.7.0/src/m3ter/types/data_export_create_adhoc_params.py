# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .data_explorer_group_param import DataExplorerGroupParam

__all__ = [
    "DataExportCreateAdhocParams",
    "AdHocOperationalDataRequest",
    "AdHocUsageDataRequest",
    "AdHocUsageDataRequestAggregation",
    "AdHocUsageDataRequestDimensionFilter",
]


class AdHocOperationalDataRequest(TypedDict, total=False):
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
    """The list of the operational data types should be exported for."""

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


class AdHocUsageDataRequest(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    source_type: Required[Annotated[Literal["USAGE"], PropertyInfo(alias="sourceType")]]
    """The type of data to export. Possible values are: USAGE"""

    account_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="accountIds")]
    """List of account IDs for which the usage data will be exported."""

    aggregations: Iterable[AdHocUsageDataRequestAggregation]
    """List of aggregations to apply"""

    dimension_filters: Annotated[Iterable[AdHocUsageDataRequestDimensionFilter], PropertyInfo(alias="dimensionFilters")]
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


class AdHocUsageDataRequestAggregation(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    field_type: Required[Annotated[Literal["DIMENSION", "MEASURE"], PropertyInfo(alias="fieldType")]]
    """Type of field"""

    function: Required[Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE"]]
    """Aggregation function"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""


class AdHocUsageDataRequestDimensionFilter(TypedDict, total=False):
    field_code: Required[Annotated[str, PropertyInfo(alias="fieldCode")]]
    """Field code"""

    meter_id: Required[Annotated[str, PropertyInfo(alias="meterId")]]
    """Meter ID"""

    values: Required[SequenceNotStr[str]]
    """Values to filter by"""


DataExportCreateAdhocParams: TypeAlias = Union[AdHocOperationalDataRequest, AdHocUsageDataRequest]
