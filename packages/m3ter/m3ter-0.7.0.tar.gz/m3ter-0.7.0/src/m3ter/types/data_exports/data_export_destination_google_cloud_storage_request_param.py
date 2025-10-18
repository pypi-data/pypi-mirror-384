# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["DataExportDestinationGoogleCloudStorageRequestParam"]


class DataExportDestinationGoogleCloudStorageRequestParam(TypedDict, total=False):
    bucket_name: Required[Annotated[str, PropertyInfo(alias="bucketName")]]
    """The export destination bucket name."""

    pool_id: Required[Annotated[str, PropertyInfo(alias="poolId")]]
    """The export destination Web Identity Federation poolId."""

    project_number: Required[Annotated[str, PropertyInfo(alias="projectNumber")]]
    """The export destination GCP projectNumber."""

    provider_id: Required[Annotated[str, PropertyInfo(alias="providerId")]]
    """The export destination Web Identity Federation identity providerId."""

    destination_type: Annotated[Literal["GCS"], PropertyInfo(alias="destinationType")]
    """The type of destination to create. Possible values are: GCS"""

    partition_order: Annotated[Optional[Literal["TYPE_FIRST", "TIME_FIRST"]], PropertyInfo(alias="partitionOrder")]
    """
    Specify how you want the file path to be structured in your bucket destination -
    by Time first (Default) or Type first.

    Type is dependent on whether the Export is for Usage data or Operational data:

    - **Usage.** Type is `measurements`.
    - **Operational.** Type is one of the entities for which operational data
      exports are available, such as `account`, `commitment`, `meter`, and so on.

    Example for Usage Data Export using .CSV format:

    - Time first:
      `{bucketName}/{prefix}/orgId={orgId}/date=2025-01-27/hour=10/type=measurements/b9a317a6-860a-40f9-9bf4-e65c44c72c94_measurements.csv.gz`
    - Type first:
      `{bucketName}/{prefix}/orgId={orgId}/type=measurements/date=2025-01-27/hour=10/b9a317a6-860a-40f9-9bf4-e65c44c72c94_measurements.csv.gz`
    """

    prefix: str
    """The export destination prefix."""

    service_account_email: Annotated[str, PropertyInfo(alias="serviceAccountEmail")]
    """The export destination service account email."""

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """
