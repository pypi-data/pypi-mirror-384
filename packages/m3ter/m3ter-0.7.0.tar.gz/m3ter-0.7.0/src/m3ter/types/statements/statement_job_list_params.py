# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["StatementJobListParams"]


class StatementJobListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    active: str
    """Boolean filter on whether to only retrieve active \\**(i.e.

    not completed/cancelled)\\** StatementJobs.

    - TRUE - only active StatementJobs retrieved.
    - FALSE - all StatementJobs retrieved.
    """

    bill_id: Annotated[str, PropertyInfo(alias="billId")]
    """Filter Statement Jobs by billId"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of StatementJobs in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of StatementJobs to retrieve per page."""

    status: str
    """Filter using the StatementJobs status. Possible values:

    - `PENDING`
    - `RUNNING`
    - `COMPLETE`
    - `CANCELLED`
    - `FAILED`
    """
