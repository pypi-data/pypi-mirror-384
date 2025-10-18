# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CommitmentFee"]


class CommitmentFee(BaseModel):
    amount: float

    date: datetime.date

    service_period_end_date: datetime.datetime = FieldInfo(alias="servicePeriodEndDate")

    service_period_start_date: datetime.datetime = FieldInfo(alias="servicePeriodStartDate")
