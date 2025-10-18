# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["AccountSearchParams"]


class AccountSearchParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    from_document: Annotated[int, PropertyInfo(alias="fromDocument")]
    """`fromDocument` for multi page retrievals."""

    operator: Literal["AND", "OR"]
    """Search Operator to be used while querying search."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Accounts to retrieve per page.

    **NOTE:** If not defined, default is 10.
    """

    search_query: Annotated[str, PropertyInfo(alias="searchQuery")]
    """Query for data using special syntax:

    - Query parameters should be delimited using the $ (dollar sign).
    - Allowed comparators are:
      - (greater than) >
      - (greater than or equal to) >=
      - (equal to) :
      - (less than) <
      - (less than or equal to) <=
      - (match phrase/prefix) ~
    - Allowed parameters are: name, code, currency, purchaseOrderNumber,
      parentAccountId, codes, id, createdBy, dtCreated, lastModifiedBy, ids.
    - Query example:
      - searchQuery=name~Premium On$currency:USD.
      - This query is translated into: find accounts whose name contains the
        phrase/prefix 'Premium On' AND the account currency is USD.

    **Note:** Using the ~ match phrase/prefix comparator. For best results, we
    recommend treating this as a "starts with" comparator for your search query.
    """

    sort_by: Annotated[str, PropertyInfo(alias="sortBy")]
    """Name of the parameter on which sorting is performed.

    Use any field available on the Account entity to sort by, such as `name`,
    `code`, and so on.
    """

    sort_order: Annotated[Literal["ASC", "DESC"], PropertyInfo(alias="sortOrder")]
    """Sorting order."""
