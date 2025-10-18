# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["IntegrationConfigurationListParams"]


class IntegrationConfigurationListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    destination_id: Annotated[str, PropertyInfo(alias="destinationId")]
    """optional filter for a specific destination"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of integration configurations in a paginated
    list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """
    Specifies the maximum number of integration configurations to retrieve per page.
    """
