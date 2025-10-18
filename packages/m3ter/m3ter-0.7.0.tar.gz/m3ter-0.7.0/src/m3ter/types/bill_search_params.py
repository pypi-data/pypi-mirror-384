# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BillSearchParams"]


class BillSearchParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    from_document: Annotated[int, PropertyInfo(alias="fromDocument")]
    """`fromDocument` for multi page retrievals."""

    operator: Literal["AND", "OR"]
    """Search Operator to be used while querying search."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Bills to retrieve per page.

    **NOTE:** If not defined, default is 10.
    """

    search_query: Annotated[str, PropertyInfo(alias="searchQuery")]
    """Query for data using special syntax:

    - Query parameters should be delimited using $ (dollar sign).
    - Allowed comparators are:
      - (greater than) >
      - (greater than or equal to) >=
      - (equal to) :
      - (less than) <
      - (less than or equal to) <=
      - (match phrase/prefix) ~
    - Allowed parameters: accountId, locked, billDate, startDate, endDate, dueDate,
      billingFrequency, id, createdBy, dtCreated, lastModifiedBy, ids.
    - Query example:
      - searchQuery=startDate>2023-01-01$accountId:62eaad67-5790-407e-b853-881564f0e543.
      - This query is translated into: find Bills that startDate is older than
        2023-01-01 AND accountId is equal to 62eaad67-5790-407e-b853-881564f0e543.

    **Note:** Using the ~ match phrase/prefix comparator. For best results, we
    recommend treating this as a "starts with" comparator for your search query.
    """

    sort_by: Annotated[str, PropertyInfo(alias="sortBy")]
    """Name of the parameter on which sorting is performed.

    Use any field available on the Bill entity to sort by, such as `accountId`,
    `endDate`, and so on.
    """

    sort_order: Annotated[Literal["ASC", "DESC"], PropertyInfo(alias="sortOrder")]
    """Sorting order."""
