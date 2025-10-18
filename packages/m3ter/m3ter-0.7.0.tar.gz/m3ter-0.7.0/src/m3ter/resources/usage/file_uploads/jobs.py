# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....pagination import SyncCursor, AsyncCursor
from ...._base_client import AsyncPaginator, make_request_options
from ....types.usage.file_uploads import job_list_params
from ....types.usage.file_uploads.file_upload_job_response import FileUploadJobResponse
from ....types.usage.file_uploads.job_get_original_download_url_response import JobGetOriginalDownloadURLResponse

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
    ) -> FileUploadJobResponse:
        """
        Get the file upload job response using the UUID of the file upload job.

        Part of the file upload service for measurements ingest.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileUploadJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date_created_end: str | Omit = omit,
        date_created_start: str | Omit = omit,
        file_key: Optional[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[FileUploadJobResponse]:
        """Lists the File Upload jobs.

        Part of the File Upload service for measurements
        ingest:

        - You can use the `dateCreatedStart` and `dateCreatedEnd` optional Query
          parameters to define a date range to filter the File Uploads jobs returned for
          this call.
        - If `dateCreatedStart` and `dateCreatedEnd` Query parameters are not used, then
          all File Upload jobs are returned.

        Args:
          date_created_end: Include only File Upload jobs created before this date. Required format is
              ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'

          date_created_start: Include only File Upload jobs created on or after this date. Required format is
              ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'

          file_key: <<deprecated>>

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of File Upload jobs to retrieve per page.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs",
            page=SyncCursor[FileUploadJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date_created_end": date_created_end,
                        "date_created_start": date_created_start,
                        "file_key": file_key,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            model=FileUploadJobResponse,
        )

    def get_original_download_url(
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
    ) -> JobGetOriginalDownloadURLResponse:
        """
        Use the original file upload job id to obtain a download URL, which you can then
        use to retrieve the file you originally uploaded to the file upload service:

        - A download URL is returned together with a download job id.
        - You can then use a `GET` using the returned download URL as the endpoint to
          retrieve the file you originally uploaded.

        Part of the file upload service for submitting measurements data files.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs/{id}/original",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=JobGetOriginalDownloadURLResponse,
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
    ) -> FileUploadJobResponse:
        """
        Get the file upload job response using the UUID of the file upload job.

        Part of the file upload service for measurements ingest.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FileUploadJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date_created_end: str | Omit = omit,
        date_created_start: str | Omit = omit,
        file_key: Optional[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[FileUploadJobResponse, AsyncCursor[FileUploadJobResponse]]:
        """Lists the File Upload jobs.

        Part of the File Upload service for measurements
        ingest:

        - You can use the `dateCreatedStart` and `dateCreatedEnd` optional Query
          parameters to define a date range to filter the File Uploads jobs returned for
          this call.
        - If `dateCreatedStart` and `dateCreatedEnd` Query parameters are not used, then
          all File Upload jobs are returned.

        Args:
          date_created_end: Include only File Upload jobs created before this date. Required format is
              ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'

          date_created_start: Include only File Upload jobs created on or after this date. Required format is
              ISO-8601: yyyy-MM-dd'T'HH:mm:ss'Z'

          file_key: <<deprecated>>

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of File Upload jobs to retrieve per page.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs",
            page=AsyncCursor[FileUploadJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date_created_end": date_created_end,
                        "date_created_start": date_created_start,
                        "file_key": file_key,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    job_list_params.JobListParams,
                ),
            ),
            model=FileUploadJobResponse,
        )

    async def get_original_download_url(
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
    ) -> JobGetOriginalDownloadURLResponse:
        """
        Use the original file upload job id to obtain a download URL, which you can then
        use to retrieve the file you originally uploaded to the file upload service:

        - A download URL is returned together with a download job id.
        - You can then use a `GET` using the returned download URL as the endpoint to
          retrieve the file you originally uploaded.

        Part of the file upload service for submitting measurements data files.

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
            f"/organizations/{org_id}/fileuploads/measurements/jobs/{id}/original",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=JobGetOriginalDownloadURLResponse,
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
        self.get_original_download_url = to_raw_response_wrapper(
            jobs.get_original_download_url,
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
        self.get_original_download_url = async_to_raw_response_wrapper(
            jobs.get_original_download_url,
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
        self.get_original_download_url = to_streamed_response_wrapper(
            jobs.get_original_download_url,
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
        self.get_original_download_url = async_to_streamed_response_wrapper(
            jobs.get_original_download_url,
        )
