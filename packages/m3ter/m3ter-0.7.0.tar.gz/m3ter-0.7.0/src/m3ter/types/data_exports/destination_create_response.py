# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .data_export_destination_response import DataExportDestinationResponse

__all__ = ["DestinationCreateResponse", "ExportDestinationS3Response", "ExportDestinationGoogleCloudStorageResponse"]


class ExportDestinationS3Response(DataExportDestinationResponse):
    id: str  # type: ignore
    """The UUID of the entity."""

    bucket_name: Optional[str] = FieldInfo(alias="bucketName", default=None)
    """Name of the S3 bucket for the Export Destination."""

    iam_role_arn: Optional[str] = FieldInfo(alias="iamRoleArn", default=None)
    """
    The specified IAM role ARN with PutObject permission for the specified
    `bucketName`, which allows the service to upload Data Exports to your S3 bucket.
    """

    partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] = FieldInfo(alias="partitionOrder", default=None)
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

    prefix: Optional[str] = None
    """Location in specified S3 bucket for the Export Destination.

    If no `prefix` is specified, then the root of the bucket is used.
    """

    version: Optional[int] = None  # type: ignore
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """


class ExportDestinationGoogleCloudStorageResponse(DataExportDestinationResponse):
    id: str  # type: ignore
    """The UUID of the entity."""

    bucket_name: Optional[str] = FieldInfo(alias="bucketName", default=None)
    """The bucket name."""

    partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] = FieldInfo(alias="partitionOrder", default=None)
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

    pool_id: Optional[str] = FieldInfo(alias="poolId", default=None)
    """The export destination Web Identity Federation poolId."""

    prefix: Optional[str] = None
    """The prefix."""

    project_number: Optional[str] = FieldInfo(alias="projectNumber", default=None)
    """The export destination GCP projectNumber."""

    provider_id: Optional[str] = FieldInfo(alias="providerId", default=None)
    """The export destination Web Identity Federation identity providerId."""

    service_account_email: Optional[str] = FieldInfo(alias="serviceAccountEmail", default=None)
    """The export destination service account email."""

    version: Optional[int] = None  # type: ignore
    """The version number:

    - **Create:** On initial Create to insert a new entity, the version is set at 1
      in the response.
    - **Update:** On successful Update, the version is incremented by 1 in the
      response.
    """


DestinationCreateResponse: TypeAlias = Union[ExportDestinationS3Response, ExportDestinationGoogleCloudStorageResponse]
