# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TransactionTypeListParams"]


class TransactionTypeListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    archived: bool
    """
    Filter with this Boolean flag whether to include TransactionTypes that are
    archived.

    - TRUE - include archived TransactionTypes in the list.
    - FALSE - exclude archived TransactionTypes.
    """

    codes: SequenceNotStr[str]
    """A list of TransactionType short codes to retrieve."""

    ids: SequenceNotStr[str]
    """A list of TransactionType unique identifiers (UUIDs) to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of TransactionTypes in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of TransactionTypes to retrieve per page."""
