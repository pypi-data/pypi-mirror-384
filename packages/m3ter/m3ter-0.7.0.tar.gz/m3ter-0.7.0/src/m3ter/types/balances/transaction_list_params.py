# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TransactionListParams"]


class TransactionListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    entity_id: Annotated[Optional[str], PropertyInfo(alias="entityId")]

    entity_type: Annotated[
        Optional[Literal["BILL", "COMMITMENT", "USER", "SERVICE_USER", "SCHEDULER"]], PropertyInfo(alias="entityType")
    ]

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi page retrievals.

    A token for retrieving the next page of transactions. You'll get this from the
    response to your request.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """The maximum number of transactions to return per page."""

    transaction_type_id: Annotated[Optional[str], PropertyInfo(alias="transactionTypeId")]
