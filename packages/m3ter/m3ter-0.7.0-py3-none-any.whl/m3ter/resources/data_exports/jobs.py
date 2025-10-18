# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform
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
from ...types.data_exports import job_list_params
from ...types.data_exports.data_export_job_response import DataExportJobResponse
from ...types.data_exports.job_get_download_url_response import JobGetDownloadURLResponse

__all__ = ["JobsResource", "AsyncJobsResource"]


class JobsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> JobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return JobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> JobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return JobsResourceWithStreamingResponse(self)

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
    ) -> DataExportJobResponse:
        """
        Retrieve an Export Job for the given UUID.

        The response returns:

        - The source type for the data exported by the Export Job: one of USAGE or
          OPERATIONAL.
        - The status of the Export Job.

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
        return self._get(
            f"/organizations/{org_id}/dataexports/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataExportJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date_created_end: str | Omit = omit,
        date_created_start: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        schedule_id: str | Omit = omit,
        status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[DataExportJobResponse]:
        """
        Retrieve a list of Export Job entities.

        Args:
          date_created_end:
              Include only Job entities created before this date. Format:
              yyyy-MM-dd'T'HH:mm:ss'Z'

          date_created_start:
              Include only Job entities created on or after this date. Format:
              yyyy-MM-dd'T'HH:mm:ss'Z'

          ids: List Job entities for the given UUIDs

          next_token: nextToken for multi page retrievals

          page_size: Number of Jobs to retrieve per page

          schedule_id: List Job entities for the schedule UUID

          status: List Job entities for the status

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
            f"/organizations/{org_id}/dataexports/jobs",
            page=SyncCursor[DataExportJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date_created_end": date_created_end,
                        "date_created_start": date_created_start,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "schedule_id": schedule_id,
                        "status": status,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            model=DataExportJobResponse,
        )

    def get_download_url(
        self,
        job_id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> JobGetDownloadURLResponse:
        """
        Returns a presigned download URL for data export file download based on the
        `jobId` provided.

        If you omit `destinationIds` when setting up your
        [Ad-Hoc data exports](https://www.m3ter.com/docs/api#tag/ExportAdHoc) or
        [Scheduled data exports](https://www.m3ter.com/docs/api#tag/ExportSchedule),
        then the data is not copied to a destination but is available for you to
        download using the returned download URL.

        **Constraints:**

        - Only valid for Export jobs ran in the past 24 hours.
        - The download URL is time-bound and is only valid for 15 minutes.

        **NOTE!** This ExportDestination endpoint is available in Beta release version.
        See
        [Feature Release Stages](https://www.m3ter.com/docs/guides/getting-started/feature-release-stages)
        for Beta release definition.

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
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return self._get(
            f"/organizations/{org_id}/dataexports/jobs/{job_id}/getdownloadurl",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=JobGetDownloadURLResponse,
        )


class AsyncJobsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncJobsResourceWithStreamingResponse(self)

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
    ) -> DataExportJobResponse:
        """
        Retrieve an Export Job for the given UUID.

        The response returns:

        - The source type for the data exported by the Export Job: one of USAGE or
          OPERATIONAL.
        - The status of the Export Job.

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
        return await self._get(
            f"/organizations/{org_id}/dataexports/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DataExportJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date_created_end: str | Omit = omit,
        date_created_start: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        schedule_id: str | Omit = omit,
        status: Literal["PENDING", "RUNNING", "SUCCEEDED", "FAILED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[DataExportJobResponse, AsyncCursor[DataExportJobResponse]]:
        """
        Retrieve a list of Export Job entities.

        Args:
          date_created_end:
              Include only Job entities created before this date. Format:
              yyyy-MM-dd'T'HH:mm:ss'Z'

          date_created_start:
              Include only Job entities created on or after this date. Format:
              yyyy-MM-dd'T'HH:mm:ss'Z'

          ids: List Job entities for the given UUIDs

          next_token: nextToken for multi page retrievals

          page_size: Number of Jobs to retrieve per page

          schedule_id: List Job entities for the schedule UUID

          status: List Job entities for the status

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
            f"/organizations/{org_id}/dataexports/jobs",
            page=AsyncCursor[DataExportJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date_created_end": date_created_end,
                        "date_created_start": date_created_start,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "schedule_id": schedule_id,
                        "status": status,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            model=DataExportJobResponse,
        )

    async def get_download_url(
        self,
        job_id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> JobGetDownloadURLResponse:
        """
        Returns a presigned download URL for data export file download based on the
        `jobId` provided.

        If you omit `destinationIds` when setting up your
        [Ad-Hoc data exports](https://www.m3ter.com/docs/api#tag/ExportAdHoc) or
        [Scheduled data exports](https://www.m3ter.com/docs/api#tag/ExportSchedule),
        then the data is not copied to a destination but is available for you to
        download using the returned download URL.

        **Constraints:**

        - Only valid for Export jobs ran in the past 24 hours.
        - The download URL is time-bound and is only valid for 15 minutes.

        **NOTE!** This ExportDestination endpoint is available in Beta release version.
        See
        [Feature Release Stages](https://www.m3ter.com/docs/guides/getting-started/feature-release-stages)
        for Beta release definition.

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
        if not job_id:
            raise ValueError(f"Expected a non-empty value for `job_id` but received {job_id!r}")
        return await self._get(
            f"/organizations/{org_id}/dataexports/jobs/{job_id}/getdownloadurl",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=JobGetDownloadURLResponse,
        )


class JobsResourceWithRawResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs

        self.retrieve = to_raw_response_wrapper(
            jobs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            jobs.list,
        )
        self.get_download_url = to_raw_response_wrapper(
            jobs.get_download_url,
        )


class AsyncJobsResourceWithRawResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs

        self.retrieve = async_to_raw_response_wrapper(
            jobs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            jobs.list,
        )
        self.get_download_url = async_to_raw_response_wrapper(
            jobs.get_download_url,
        )


class JobsResourceWithStreamingResponse:
    def __init__(self, jobs: JobsResource) -> None:
        self._jobs = jobs

        self.retrieve = to_streamed_response_wrapper(
            jobs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            jobs.list,
        )
        self.get_download_url = to_streamed_response_wrapper(
            jobs.get_download_url,
        )


class AsyncJobsResourceWithStreamingResponse:
    def __init__(self, jobs: AsyncJobsResource) -> None:
        self._jobs = jobs

        self.retrieve = async_to_streamed_response_wrapper(
            jobs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            jobs.list,
        )
        self.get_download_url = async_to_streamed_response_wrapper(
            jobs.get_download_url,
        )
