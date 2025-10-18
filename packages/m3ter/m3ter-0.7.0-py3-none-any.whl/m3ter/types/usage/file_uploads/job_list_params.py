# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["JobListParams"]


class JobListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    date_created_end: Annotated[str, PropertyInfo(alias="dateCreatedEnd")]
    """Include only File Upload jobs created before this date.

    Required format is ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'
    """

    date_created_start: Annotated[str, PropertyInfo(alias="dateCreatedStart")]
    """Include only File Upload jobs created on or after this date.

    Required format is ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'
    """

    file_key: Annotated[Optional[str], PropertyInfo(alias="fileKey")]
    """<<deprecated>>"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of File Upload jobs to retrieve per page."""
