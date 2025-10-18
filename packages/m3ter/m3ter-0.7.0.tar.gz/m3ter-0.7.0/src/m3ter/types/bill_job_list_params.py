# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BillJobListParams"]


class BillJobListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    active: str
    """
    Boolean filter to retrieve only active BillJobs and exclude completed or
    cancelled BillJobs from the results.

    - TRUE - only active BillJobs.
    - FALSE - all BillJobs including completed and cancelled BillJobs.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of BillJobs in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of BillJobs to retrieve per page."""

    status: str
    """Filter BillJobs by specific status.

    Allows for targeted retrieval of BillJobs based on their current processing
    status.

    Possible states are:

    - PENDING
    - INITIALIZING
    - RUNNING
    - COMPLETE
    - CANCELLED
    """
