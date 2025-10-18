# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["IntegrationConfigurationGetByEntityParams"]


class IntegrationConfigurationGetByEntityParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    destination: str
    """Destination type to retrieve IntegrationConfigs for"""

    destination_id: Annotated[str, PropertyInfo(alias="destinationId")]
    """UUID of the destination to retrieve IntegrationConfigs for"""

    entity_id: Annotated[str, PropertyInfo(alias="entityId")]
    """UUID of the entity to retrieve IntegrationConfigs for"""
