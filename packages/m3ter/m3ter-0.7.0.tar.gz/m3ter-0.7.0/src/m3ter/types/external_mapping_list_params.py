# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["ExternalMappingListParams"]


class ExternalMappingListParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    external_system_id: Annotated[str, PropertyInfo(alias="externalSystemId")]
    """The name of the external system to use as a filter.

    For example, if you want to list only those external mappings created for your
    Organization for the Salesforce external system, use:

    `?externalSystemId=Salesforce`
    """

    integration_config_id: Annotated[str, PropertyInfo(alias="integrationConfigId")]
    """ID of the integration config"""

    m3ter_ids: Annotated[SequenceNotStr[str], PropertyInfo(alias="m3terIds")]
    """IDs for m3ter entities"""

    next_token: Annotated[str, PropertyInfo(alias="nextToken")]
    """The `nextToken` for multi-page retrievals.

    It is used to fetch the next page of External Mappings in a paginated list.
    """

    page_size: Annotated[int, PropertyInfo(alias="pageSize")]
    """Specifies the maximum number of External Mappings to retrieve per page."""
