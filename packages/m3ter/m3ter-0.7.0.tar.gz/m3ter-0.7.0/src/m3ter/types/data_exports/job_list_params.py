# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["JobListParams"]


class JobListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    date_created_end: Annotated[str, PropertyInfo(alias="dateCreatedEnd")]
    """Include only Job entities created before this date.

    Format: yyyy-MM-dd'T'HH:mm:ss'Z'
    """

    date_created_start: Annotated[str, PropertyInfo(alias="dateCreatedStart")]
    """Include only Job entities created on or after this date.

    Format: yyyy-MM-dd'T'HH:mm:ss'Z'
    """

    ids: SequenceNotStr[str]
    """List Job entities for the given UUIDs"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """nextToken for multi page retrievals"""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Jobs to retrieve per page"""

    schedule_id: Annotated[str, PropertyInfo(alias="scheduleId")]
    """List Job entities for the schedule UUID"""

    status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"]
    """List Job entities for the status"""
