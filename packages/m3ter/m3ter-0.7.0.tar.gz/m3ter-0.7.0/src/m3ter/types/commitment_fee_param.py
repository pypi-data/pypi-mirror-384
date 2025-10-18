# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import datetime
from typing import Union
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["CommitmentFeeParam"]


class CommitmentFeeParam(TypedDict, total=False):
    amount: Required[float]

    date: Required[Annotated[Union[str, datetime.date], PropertyInfo(format="iso8601")]]

    service_period_end_date: Required[
        Annotated[Union[str, datetime.datetime], PropertyInfo(alias="servicePeriodEndDate", format="iso8601")]
    ]

    service_period_start_date: Required[
        Annotated[Union[str, datetime.datetime], PropertyInfo(alias="servicePeriodStartDate", format="iso8601")]
    ]
