# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["ContractListParams"]


class ContractListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[Optional[str], PropertyInfo(alias="accountId")]

    codes: SequenceNotStr[str]
    """
    An optional parameter to retrieve specific Contracts based on their short codes.
    """

    ids: SequenceNotStr[str]
    """
    An optional parameter to filter the list based on specific Contract unique
    identifiers (UUIDs).
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Contracts in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of Contracts to retrieve per page."""
