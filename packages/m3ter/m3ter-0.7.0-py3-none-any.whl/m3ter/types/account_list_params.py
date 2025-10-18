# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["AccountListParams"]


class AccountListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    codes: SequenceNotStr[str]
    """List of Account Codes to retrieve.

    These are unique short codes for each Account.
    """

    ids: SequenceNotStr[str]
    """List of Account IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi-page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of accounts to retrieve per page."""
