# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["DebitReasonListParams"]


class DebitReasonListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    archived: bool
    """Filter using the boolean archived flag.

    DebitReasons can be archived if they are obsolete.

    - TRUE includes DebitReasons that have been archived.
    - FALSE excludes archived DebitReasons.
    """

    codes: SequenceNotStr[str]
    """List of Debit Reason short codes to retrieve."""

    ids: SequenceNotStr[str]
    """List of Debit Reason IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Debit Reasons to retrieve per page."""
