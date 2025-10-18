# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["MeterListParams"]


class MeterListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    codes: SequenceNotStr[str]
    """List of Meter codes to retrieve.

    These are the unique short codes that identify each Meter.
    """

    ids: SequenceNotStr[str]
    """List of Meter IDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """`nextToken` for multi page retrievals."""

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Number of Meters to retrieve per page."""

    product_id: Annotated[SequenceNotStr[str], PropertyInfo(alias="productId")]
    """The UUIDs of the Products to retrieve Meters for."""
