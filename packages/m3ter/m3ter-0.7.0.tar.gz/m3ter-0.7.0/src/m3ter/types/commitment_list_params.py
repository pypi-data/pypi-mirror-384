# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["CommitmentListParams"]


class CommitmentListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    account_id: Annotated[str, PropertyInfo(alias="accountId")]
    """The unique identifier (UUID) for the Account.

    This parameter helps filter the Commitments related to a specific end-customer
    Account.
    """

    contract_id: Annotated[Optional[str], PropertyInfo(alias="contractId")]

    date: str
    """
    A date _(in ISO-8601 format)_ to filter Commitments which are active on this
    specific date.
    """

    end_date_end: Annotated[str, PropertyInfo(alias="endDateEnd")]
    """A date _(in ISO-8601 format)_ used to filter Commitments.

    Only Commitments with end dates before this date will be included.
    """

    end_date_start: Annotated[str, PropertyInfo(alias="endDateStart")]
    """A date _(in ISO-8601 format)_ used to filter Commitments.

    Only Commitments with end dates on or after this date will be included.
    """

    ids: SequenceNotStr[str]
    """A list of unique identifiers (UUIDs) for the Commitments to retrieve.

    Use this to fetch specific Commitments in a single request.
    """

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of Commitments in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of Commitments to retrieve per page."""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """The unique identifier (UUID) for the Product.

    This parameter helps filter the Commitments related to a specific Product.
    """
