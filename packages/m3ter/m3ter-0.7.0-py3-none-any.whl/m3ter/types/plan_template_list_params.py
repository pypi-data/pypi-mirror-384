# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["PlanTemplateListParams"]


class PlanTemplateListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    ids: SequenceNotStr[str]
    """List of specific PlanTemplate UUIDs to retrieve."""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of PlanTemplates in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of PlanTemplates to retrieve per page."""

    product_id: Annotated[str, PropertyInfo(alias="productId")]
    """
    The unique identifiers (UUIDs) of the Products to retrieve associated
    PlanTemplates.
    """
