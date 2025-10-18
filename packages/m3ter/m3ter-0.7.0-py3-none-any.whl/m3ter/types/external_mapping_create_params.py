# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["ExternalMappingCreateParams"]


class ExternalMappingCreateParams(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    external_id: Required[Annotated[str, PropertyInfo(alias="externalId")]]
    """The unique identifier (UUID) of the entity in the external system.

    This UUID should already exist in the external system.
    """

    external_system: Required[Annotated[str, PropertyInfo(alias="externalSystem")]]
    """The name of the external system where the entity you are mapping resides."""

    external_table: Required[Annotated[str, PropertyInfo(alias="externalTable")]]
    """The name of the table in ther external system where the entity resides."""

    m3ter_entity: Required[Annotated[str, PropertyInfo(alias="m3terEntity")]]
    """
    The name of the m3ter entity that you are creating or modifying an External
    Mapping for. As an example, this could be an "Account".
    """

    m3ter_id: Required[Annotated[str, PropertyInfo(alias="m3terId")]]
    """The unique identifier (UUID) of the m3ter entity."""

    integration_config_id: Annotated[str, PropertyInfo(alias="integrationConfigId")]
    """UUID of the integration config to link this mapping to"""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
