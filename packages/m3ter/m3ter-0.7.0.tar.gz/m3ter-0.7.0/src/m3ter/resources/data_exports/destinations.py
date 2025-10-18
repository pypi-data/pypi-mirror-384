# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, Optional, cast
from typing_extensions import Literal, overload

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import required_args, maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursor, AsyncCursor
from ..._base_client import AsyncPaginator, make_request_options
from ...types.data_exports import destination_list_params, destination_create_params, destination_update_params
from ...types.data_exports.destination_create_response import DestinationCreateResponse
from ...types.data_exports.destination_delete_response import DestinationDeleteResponse
from ...types.data_exports.destination_update_response import DestinationUpdateResponse
from ...types.data_exports.destination_retrieve_response import DestinationRetrieveResponse
from ...types.data_exports.data_export_destination_response import DataExportDestinationResponse

__all__ = ["DestinationsResource", "AsyncDestinationsResource"]


class DestinationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DestinationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DestinationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DestinationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return DestinationsResourceWithStreamingResponse(self)

    @overload
    def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str,
        destination_type: Literal["S3"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        """
        Create a new Export Destination to use for your Data Export Schedules or Ad-Hoc
        Data Exports.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: Name of the S3 bucket for the Export Destination.

          iam_role_arn: To enable m3ter to upload a Data Exports to your S3 bucket, the service has to
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

          destination_type: The type of destination to create. Possible values are: S3

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: Location in specified S3 bucket for the Export Destination. If you omit a
              `prefix`, then the root of the bucket will be used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        pool_id: str,
        project_number: str,
        provider_id: str,
        destination_type: Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        service_account_email: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        """
        Create a new Export Destination to use for your Data Export Schedules or Ad-Hoc
        Data Exports.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: The export destination bucket name.

          pool_id: The export destination Web Identity Federation poolId.

          project_number: The export destination GCP projectNumber.

          provider_id: The export destination Web Identity Federation identity providerId.

          destination_type: The type of destination to create. Possible values are: GCS

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: The export destination prefix.

          service_account_email: The export destination service account email.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["bucket_name", "iam_role_arn"], ["bucket_name", "pool_id", "project_number", "provider_id"])
    def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str | Omit = omit,
        destination_type: Literal["S3"] | Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        pool_id: str | Omit = omit,
        project_number: str | Omit = omit,
        provider_id: str | Omit = omit,
        service_account_email: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return cast(
            DestinationCreateResponse,
            self._post(
                f"/organizations/{org_id}/dataexports/destinations",
                body=maybe_transform(
                    {
                        "bucket_name": bucket_name,
                        "iam_role_arn": iam_role_arn,
                        "destination_type": destination_type,
                        "partition_order": partition_order,
                        "prefix": prefix,
                        "version": version,
                        "pool_id": pool_id,
                        "project_number": project_number,
                        "provider_id": provider_id,
                        "service_account_email": service_account_email,
                    },
                    destination_create_params.DestinationCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationCreateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationRetrieveResponse:
        """
        Retrieve an Export Destination for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationRetrieveResponse,
            self._get(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    @overload
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str,
        destination_type: Literal["S3"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        """
        Update an Export Destination for the given UUID.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: Name of the S3 bucket for the Export Destination.

          iam_role_arn: To enable m3ter to upload a Data Exports to your S3 bucket, the service has to
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

          destination_type: The type of destination to create. Possible values are: S3

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: Location in specified S3 bucket for the Export Destination. If you omit a
              `prefix`, then the root of the bucket will be used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        pool_id: str,
        project_number: str,
        provider_id: str,
        destination_type: Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        service_account_email: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        """
        Update an Export Destination for the given UUID.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: The export destination bucket name.

          pool_id: The export destination Web Identity Federation poolId.

          project_number: The export destination GCP projectNumber.

          provider_id: The export destination Web Identity Federation identity providerId.

          destination_type: The type of destination to create. Possible values are: GCS

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: The export destination prefix.

          service_account_email: The export destination service account email.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["bucket_name", "iam_role_arn"], ["bucket_name", "pool_id", "project_number", "provider_id"])
    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str | Omit = omit,
        destination_type: Literal["S3"] | Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        pool_id: str | Omit = omit,
        project_number: str | Omit = omit,
        provider_id: str | Omit = omit,
        service_account_email: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationUpdateResponse,
            self._put(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                body=maybe_transform(
                    {
                        "bucket_name": bucket_name,
                        "iam_role_arn": iam_role_arn,
                        "destination_type": destination_type,
                        "partition_order": partition_order,
                        "prefix": prefix,
                        "version": version,
                        "pool_id": pool_id,
                        "project_number": project_number,
                        "provider_id": provider_id,
                        "service_account_email": service_account_email,
                    },
                    destination_update_params.DestinationUpdateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationUpdateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[DataExportDestinationResponse]:
        """Retrieve a list of Export Destination entities.

        You can filter the list of
        Destinations returned by UUID.

        Args:
          ids: List of Export Destination UUIDs to retrieve.

          next_token: nextToken for multi page retrievals

          page_size: Number of returned Export Destinations to list per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/dataexports/destinations",
            page=SyncCursor[DataExportDestinationResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    destination_list_params.DestinationListParams,
                ),
            ),
            model=DataExportDestinationResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationDeleteResponse:
        """
        Delete an Export Destination for the given UUID.

        **NOTE:** If you attempt to delete an Export Destination that is currently
        linked to a Data Export Schedule, an error message is returned and you won't be
        able to delete the Destination.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationDeleteResponse,
            self._delete(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationDeleteResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class AsyncDestinationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDestinationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDestinationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDestinationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncDestinationsResourceWithStreamingResponse(self)

    @overload
    async def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str,
        destination_type: Literal["S3"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        """
        Create a new Export Destination to use for your Data Export Schedules or Ad-Hoc
        Data Exports.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: Name of the S3 bucket for the Export Destination.

          iam_role_arn: To enable m3ter to upload a Data Exports to your S3 bucket, the service has to
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

          destination_type: The type of destination to create. Possible values are: S3

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: Location in specified S3 bucket for the Export Destination. If you omit a
              `prefix`, then the root of the bucket will be used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        pool_id: str,
        project_number: str,
        provider_id: str,
        destination_type: Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        service_account_email: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        """
        Create a new Export Destination to use for your Data Export Schedules or Ad-Hoc
        Data Exports.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: The export destination bucket name.

          pool_id: The export destination Web Identity Federation poolId.

          project_number: The export destination GCP projectNumber.

          provider_id: The export destination Web Identity Federation identity providerId.

          destination_type: The type of destination to create. Possible values are: GCS

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: The export destination prefix.

          service_account_email: The export destination service account email.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["bucket_name", "iam_role_arn"], ["bucket_name", "pool_id", "project_number", "provider_id"])
    async def create(
        self,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str | Omit = omit,
        destination_type: Literal["S3"] | Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        pool_id: str | Omit = omit,
        project_number: str | Omit = omit,
        provider_id: str | Omit = omit,
        service_account_email: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationCreateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return cast(
            DestinationCreateResponse,
            await self._post(
                f"/organizations/{org_id}/dataexports/destinations",
                body=await async_maybe_transform(
                    {
                        "bucket_name": bucket_name,
                        "iam_role_arn": iam_role_arn,
                        "destination_type": destination_type,
                        "partition_order": partition_order,
                        "prefix": prefix,
                        "version": version,
                        "pool_id": pool_id,
                        "project_number": project_number,
                        "provider_id": provider_id,
                        "service_account_email": service_account_email,
                    },
                    destination_create_params.DestinationCreateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationCreateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationRetrieveResponse:
        """
        Retrieve an Export Destination for the given UUID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationRetrieveResponse,
            await self._get(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationRetrieveResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    @overload
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str,
        destination_type: Literal["S3"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        """
        Update an Export Destination for the given UUID.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: Name of the S3 bucket for the Export Destination.

          iam_role_arn: To enable m3ter to upload a Data Exports to your S3 bucket, the service has to
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

          destination_type: The type of destination to create. Possible values are: S3

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: Location in specified S3 bucket for the Export Destination. If you omit a
              `prefix`, then the root of the bucket will be used.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @overload
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        pool_id: str,
        project_number: str,
        provider_id: str,
        destination_type: Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        service_account_email: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        """
        Update an Export Destination for the given UUID.

        Currently, two options for setting up Data Export Destinations are available:

        - S3 buckets on your AWS account.
        - Buckets in your Google Cloud Storage account.

        Request and Response schema:

        - Use the selector under the `destinationType` parameter to expose the relevant
          request and response schema for the type of Destination.

        Request and Response samples:

        - Use the **Example** selector to show the relevant request and response samples
          for the type of Destination.

        Args:
          bucket_name: The export destination bucket name.

          pool_id: The export destination Web Identity Federation poolId.

          project_number: The export destination GCP projectNumber.

          provider_id: The export destination Web Identity Federation identity providerId.

          destination_type: The type of destination to create. Possible values are: GCS

          partition_order: Specify how you want the file path to be structured in your bucket destination -
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

          prefix: The export destination prefix.

          service_account_email: The export destination service account email.

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - _do not use
                for Create_. On initial Create, version is set at 1 and listed in the
                response.
              - **Update Entity:** On Update, version is required and must match the existing
                version because a check is performed to ensure sequential versioning is
                preserved. Version is incremented by 1 and listed in the response.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        ...

    @required_args(["bucket_name", "iam_role_arn"], ["bucket_name", "pool_id", "project_number", "provider_id"])
    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bucket_name: str,
        iam_role_arn: str | Omit = omit,
        destination_type: Literal["S3"] | Literal["GCS"] | Omit = omit,
        partition_order: Optional[Literal["TYPE_FIRST", "TIME_FIRST"]] | Omit = omit,
        prefix: str | Omit = omit,
        version: int | Omit = omit,
        pool_id: str | Omit = omit,
        project_number: str | Omit = omit,
        provider_id: str | Omit = omit,
        service_account_email: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationUpdateResponse:
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationUpdateResponse,
            await self._put(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                body=await async_maybe_transform(
                    {
                        "bucket_name": bucket_name,
                        "iam_role_arn": iam_role_arn,
                        "destination_type": destination_type,
                        "partition_order": partition_order,
                        "prefix": prefix,
                        "version": version,
                        "pool_id": pool_id,
                        "project_number": project_number,
                        "provider_id": provider_id,
                        "service_account_email": service_account_email,
                    },
                    destination_update_params.DestinationUpdateParams,
                ),
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationUpdateResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[DataExportDestinationResponse, AsyncCursor[DataExportDestinationResponse]]:
        """Retrieve a list of Export Destination entities.

        You can filter the list of
        Destinations returned by UUID.

        Args:
          ids: List of Export Destination UUIDs to retrieve.

          next_token: nextToken for multi page retrievals

          page_size: Number of returned Export Destinations to list per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/dataexports/destinations",
            page=AsyncCursor[DataExportDestinationResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    destination_list_params.DestinationListParams,
                ),
            ),
            model=DataExportDestinationResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DestinationDeleteResponse:
        """
        Delete an Export Destination for the given UUID.

        **NOTE:** If you attempt to delete an Export Destination that is currently
        linked to a Data Export Schedule, an error message is returned and you won't be
        able to delete the Destination.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return cast(
            DestinationDeleteResponse,
            await self._delete(
                f"/organizations/{org_id}/dataexports/destinations/{id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, DestinationDeleteResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class DestinationsResourceWithRawResponse:
    def __init__(self, destinations: DestinationsResource) -> None:
        self._destinations = destinations

        self.create = to_raw_response_wrapper(
            destinations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            destinations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            destinations.update,
        )
        self.list = to_raw_response_wrapper(
            destinations.list,
        )
        self.delete = to_raw_response_wrapper(
            destinations.delete,
        )


class AsyncDestinationsResourceWithRawResponse:
    def __init__(self, destinations: AsyncDestinationsResource) -> None:
        self._destinations = destinations

        self.create = async_to_raw_response_wrapper(
            destinations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            destinations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            destinations.update,
        )
        self.list = async_to_raw_response_wrapper(
            destinations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            destinations.delete,
        )


class DestinationsResourceWithStreamingResponse:
    def __init__(self, destinations: DestinationsResource) -> None:
        self._destinations = destinations

        self.create = to_streamed_response_wrapper(
            destinations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            destinations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            destinations.update,
        )
        self.list = to_streamed_response_wrapper(
            destinations.list,
        )
        self.delete = to_streamed_response_wrapper(
            destinations.delete,
        )


class AsyncDestinationsResourceWithStreamingResponse:
    def __init__(self, destinations: AsyncDestinationsResource) -> None:
        self._destinations = destinations

        self.create = async_to_streamed_response_wrapper(
            destinations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            destinations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            destinations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            destinations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            destinations.delete,
        )
