# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .measurement_request_param import MeasurementRequestParam

__all__ = ["UsageSubmitParams"]


class UsageSubmitParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    measurements: Required[Iterable[MeasurementRequestParam]]
    """Request containing the usage data measurements for submission."""
