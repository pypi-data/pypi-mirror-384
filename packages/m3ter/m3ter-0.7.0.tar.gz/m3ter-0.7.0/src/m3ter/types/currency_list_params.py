# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["CurrencyListParams"]


class CurrencyListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    archived: bool
    """Filter by archived flag.

    A True / False flag indicating whether to return Currencies that are archived
    _(obsolete)_.

    - TRUE - return archived Currencies.
    - FALSE - archived Currencies are not returned.
    """

    codes: SequenceNotStr[str]
    """
    An optional parameter to retrieve specific Currencies based on their short
    codes.
    """

    ids: SequenceNotStr[str]
    """
    An optional parameter to filter the list based on specific Currency unique
    identifiers (UUIDs).
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Currencies in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of Currencies to retrieve per page."""
