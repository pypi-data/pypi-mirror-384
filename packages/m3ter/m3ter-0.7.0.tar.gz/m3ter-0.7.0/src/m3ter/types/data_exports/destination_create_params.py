# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from ..._utils import PropertyInfo

__all__ = [
    "DestinationCreateParams",
    "DataExportDestinationS3Request",
    "DataExportDestinationGoogleCloudStorageRequest",
]


class DataExportDestinationS3Request(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

    bucket_name: Required[Annotated[str, PropertyInfo(alias="bucketName")]]
    """Name of the S3 bucket for the Export Destination."""

    iam_role_arn: Required[Annotated[str, PropertyInfo(alias="iamRoleArn")]]
    """
    To enable m3ter to upload a Data Exports to your S3 bucket, the service has to
    assume an IAM role with PutObject permission for the specified `bucketName`.
    Create a suitable IAM role in your AWS account and enter ARN:

    **Formatting Constraints:**

    - The IAM role ARN must begin with "arn:aws:iam".
    - The general format required is:
      "arn:aws:iam::<aws account id>:role/<role name>". For example:
      "arn:aws:iam::922609978421:role/IAMRole636".
    - If the `iamRoleArn` used doesn't comply with this format, then an error
      message will be returned.

    **More Details:** For more details and examples of the Permission and Trust
    Policies you can use to create the required IAM Role ARN, see
    [Creating Data Export Destinations](https://www.m3ter.com/docs/guides/data-exports/creating-data-export-destinations)
    in our main User documentation.
    """

    destination_type: Annotated[Literal["S3"], PropertyInfo(alias="destinationType")]
    """The type of destination to create. Possible values are: S3"""

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
    """Location in specified S3 bucket for the Export Destination.

    If you omit a `prefix`, then the root of the bucket will be used.
    """

    version: int
    """The version number of the entity:

    - **Create entity:** Not valid for initial insertion of new entity - _do not use
      for Create_. On initial Create, version is set at 1 and listed in the
      response.
    - **Update Entity:** On Update, version is required and must match the existing
      version because a check is performed to ensure sequential versioning is
      preserved. Version is incremented by 1 and listed in the response.
    """


class DataExportDestinationGoogleCloudStorageRequest(TypedDict, total=False):
    org_id: Annotated[str, PropertyInfo(alias="orgId")]

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


DestinationCreateParams: TypeAlias = Union[
    DataExportDestinationS3Request, DataExportDestinationGoogleCloudStorageRequest
]
