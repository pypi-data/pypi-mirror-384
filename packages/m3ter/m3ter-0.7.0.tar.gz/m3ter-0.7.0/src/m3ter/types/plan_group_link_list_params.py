# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["PlanGroupLinkListParams"]


class PlanGroupLinkListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    ids: SequenceNotStr[str]
    """list of IDs to retrieve"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of PlanGroupLinks to retrieve per page"""

    plan: str
    """UUID of the Plan to retrieve PlanGroupLinks for"""

    plan_group: Annotated[str, PropertyInfo(alias="planGroup")]
    """UUID of the PlanGroup to retrieve PlanGroupLinks for"""
