# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["OperationalDataExportScheduleRequestParam"]


class OperationalDataExportScheduleRequestParam(TypedDict, total=False):
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
