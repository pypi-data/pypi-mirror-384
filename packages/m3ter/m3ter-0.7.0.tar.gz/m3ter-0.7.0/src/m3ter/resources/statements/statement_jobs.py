# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
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
from ...types.statements import (
    statement_job_list_params,
    statement_job_create_params,
    statement_job_create_batch_params,
)
from ...types.statements.statement_job_response import StatementJobResponse
from ...types.statements.statement_job_create_batch_response import StatementJobCreateBatchResponse

__all__ = ["StatementJobsResource", "AsyncStatementJobsResource"]


class StatementJobsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StatementJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return StatementJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StatementJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return StatementJobsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        bill_id: str,
        include_csv_format: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementJobResponse:
        """
        This endpoint creates a StatementJob for a single bill within an Organization
        using the Bill UUID.

        The Bill Statement is generated asynchronously:

        - The default format for generating the Statement is in JSON format and
          according to the Bill Statement Definition you've specified at either
          Organization level or Account level.
        - If you also want to generate the Statement in CSV format, use the
          `includeCsvFormat` request body parameter.
        - The response body provides a time-bound pre-signed URL, which you can use to
          download the JSON format Statement.
        - When you have generated a Statement for a Bill, you can also obtain a
          time-bound pre-signed download URL using either the
          [Retrieve Bill Statement in JSON Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillJsonStatement)
          and
          [Retrieve Bill Statement in CSV Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillCsvStatement)
          calls found in the [Bill](https://www.m3ter.com/docs/api#tag/Bill) section of
          this API Reference.

        **Notes:**

        - If the response to the Create StatementJob call shows the `statementJobStatus`
          as `PENDING` or `RUNNING`, you will not receive the pre-signed URL in the
          response. Wait a few minutes to allow the StatementJob to complete and then
          use the
          [Get StatmentJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/GetStatementJob)
          call in this section to obtain the pre-signed download URL for the generated
          Bill Statement.
        - When you have submitted a StatementJob and a Bill Statement has been
          generated, you can also download the Statement directly from a Bill Details
          page in the Console. See
          [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
          in our user Documentation.

        Args:
          bill_id: The unique identifier (UUID) of the bill associated with the StatementJob.

          include_csv_format: A Boolean value indicating whether the generated statement includes a CSV
              format.

              - TRUE - includes the statement in CSV format.
              - FALSE - no CSV format statement.

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
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._post(
            f"/organizations/{org_id}/statementjobs",
            body=maybe_transform(
                {
                    "bill_id": bill_id,
                    "include_csv_format": include_csv_format,
                    "version": version,
                },
                statement_job_create_params.StatementJobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
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
    ) -> StatementJobResponse:
        """
        Retrieves the details of a specific StatementJob using its UUID.

        Use this call to obtain the time-bound pre-signed download URL for the generated
        Bill Statement if the initial
        [Create StatementJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/CreateStatementJob)
        returned a response showing the `statementJobStatus` not yet complete and as
        `PENDING` or `RUNNING`.

        **Note:** When you have submitted a StatementJob and a Bill Statement has been
        generated, you can also download the Statement directly from a Bill Details page
        in the Console. See
        [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
        in our user Documentation.

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
            f"/organizations/{org_id}/statementjobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: str | Omit = omit,
        bill_id: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[StatementJobResponse]:
        """
        Retrieve a list of StatementJobs.

        Retrieves a list of all StatementJobs for a specific Organization. You can
        filter the results based on:

        - StatementJob status.
        - Whether StatementJob is neither completed nor cancelled but remains active.
        - The ID of the Bill the StatementJob is associated with.

        You can also paginate the results for easier management.

        **WARNING!**

        - You can use only one of the valid Query parameters: `active`, `status`, or
          `billId` in any call. If you use more than one of these Query parameters in
          the same call, then a 400 Bad Request is returned with an error message.

        Args:
          active: Boolean filter on whether to only retrieve active _(i.e. not
              completed/cancelled)_ StatementJobs.

              - TRUE - only active StatementJobs retrieved.
              - FALSE - all StatementJobs retrieved.

          bill_id: Filter Statement Jobs by billId

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              StatementJobs in a paginated list.

          page_size: Specifies the maximum number of StatementJobs to retrieve per page.

          status:
              Filter using the StatementJobs status. Possible values:

              - `PENDING`
              - `RUNNING`
              - `COMPLETE`
              - `CANCELLED`
              - `FAILED`

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
            f"/organizations/{org_id}/statementjobs",
            page=SyncCursor[StatementJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "bill_id": bill_id,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    statement_job_list_params.StatementJobListParams,
                ),
            ),
            model=StatementJobResponse,
        )

    def cancel(
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
    ) -> StatementJobResponse:
        """
        Cancel the StatementJob with the given UUID.

        Use this endpoint to halt the execution of a specific StatementJob identified by
        its UUID. This operation may be useful if you need to stop a StatementJob due to
        unforeseen issues or changes.

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
        return self._post(
            f"/organizations/{org_id}/statementjobs/{id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
        )

    def create_batch(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        include_csv_format: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementJobCreateBatchResponse:
        """
        Create a batch of StatementJobs for multiple bills.

        Initiate the creation of multiple StatementJobs asynchronously for the list of
        bills with the given UUIDs:

        - The default format for generating Bill Statements is in JSON format and
          according to the Bill Statement Definition you've specified at either
          Organization level or Account level.
        - If you also want to generate the Statements in CSV format, use the
          `includeCsvFormat` request body parameter.
        - The response body provides a time-bound pre-signed URL, which you can use to
          download the JSON format Statement.
        - When you have generated a Statement for a Bill, you can also obtain a
          time-bound pre-signed download URL using either the
          [Retrieve Bill Statement in JSON Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillJsonStatement)
          and
          [Retrieve Bill Statement in CSV Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillCsvStatement)
          calls found in the [Bill](https://www.m3ter.com/docs/api#tag/Bill) section of
          this API Reference.

        **Notes:**

        - If the response to the Create StatementJob call shows the `statementJobStatus`
          as `PENDING` or `RUNNING`, you will not receive the pre-signed URL in the
          response. Wait a few minutes to allow the StatementJob to complete and then
          use the
          [Get StatmentJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/GetStatementJob)
          call in this section to obtain the pre-signed download URL for the generated
          Bill Statement.
        - When you have submitted a StatementJob and a Bill Statement has been
          generated, you can also download the Statement directly from a Bill Details
          page in the Console. See
          [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
          in our user Documentation.

        Args:
          bill_ids: The list of unique identifiers (UUIDs) of the bills associated with the
              StatementJob.

          include_csv_format: A Boolean value indicating whether the generated statement includes a CSV
              format.

              - TRUE - includes the statement in CSV format.
              - FALSE - no CSV format statement.

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
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._post(
            f"/organizations/{org_id}/statementjobs/batch",
            body=maybe_transform(
                {
                    "bill_ids": bill_ids,
                    "include_csv_format": include_csv_format,
                    "version": version,
                },
                statement_job_create_batch_params.StatementJobCreateBatchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobCreateBatchResponse,
        )


class AsyncStatementJobsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStatementJobsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStatementJobsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStatementJobsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncStatementJobsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        bill_id: str,
        include_csv_format: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementJobResponse:
        """
        This endpoint creates a StatementJob for a single bill within an Organization
        using the Bill UUID.

        The Bill Statement is generated asynchronously:

        - The default format for generating the Statement is in JSON format and
          according to the Bill Statement Definition you've specified at either
          Organization level or Account level.
        - If you also want to generate the Statement in CSV format, use the
          `includeCsvFormat` request body parameter.
        - The response body provides a time-bound pre-signed URL, which you can use to
          download the JSON format Statement.
        - When you have generated a Statement for a Bill, you can also obtain a
          time-bound pre-signed download URL using either the
          [Retrieve Bill Statement in JSON Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillJsonStatement)
          and
          [Retrieve Bill Statement in CSV Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillCsvStatement)
          calls found in the [Bill](https://www.m3ter.com/docs/api#tag/Bill) section of
          this API Reference.

        **Notes:**

        - If the response to the Create StatementJob call shows the `statementJobStatus`
          as `PENDING` or `RUNNING`, you will not receive the pre-signed URL in the
          response. Wait a few minutes to allow the StatementJob to complete and then
          use the
          [Get StatmentJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/GetStatementJob)
          call in this section to obtain the pre-signed download URL for the generated
          Bill Statement.
        - When you have submitted a StatementJob and a Bill Statement has been
          generated, you can also download the Statement directly from a Bill Details
          page in the Console. See
          [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
          in our user Documentation.

        Args:
          bill_id: The unique identifier (UUID) of the bill associated with the StatementJob.

          include_csv_format: A Boolean value indicating whether the generated statement includes a CSV
              format.

              - TRUE - includes the statement in CSV format.
              - FALSE - no CSV format statement.

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
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._post(
            f"/organizations/{org_id}/statementjobs",
            body=await async_maybe_transform(
                {
                    "bill_id": bill_id,
                    "include_csv_format": include_csv_format,
                    "version": version,
                },
                statement_job_create_params.StatementJobCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
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
    ) -> StatementJobResponse:
        """
        Retrieves the details of a specific StatementJob using its UUID.

        Use this call to obtain the time-bound pre-signed download URL for the generated
        Bill Statement if the initial
        [Create StatementJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/CreateStatementJob)
        returned a response showing the `statementJobStatus` not yet complete and as
        `PENDING` or `RUNNING`.

        **Note:** When you have submitted a StatementJob and a Bill Statement has been
        generated, you can also download the Statement directly from a Bill Details page
        in the Console. See
        [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
        in our user Documentation.

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
            f"/organizations/{org_id}/statementjobs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: str | Omit = omit,
        bill_id: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[StatementJobResponse, AsyncCursor[StatementJobResponse]]:
        """
        Retrieve a list of StatementJobs.

        Retrieves a list of all StatementJobs for a specific Organization. You can
        filter the results based on:

        - StatementJob status.
        - Whether StatementJob is neither completed nor cancelled but remains active.
        - The ID of the Bill the StatementJob is associated with.

        You can also paginate the results for easier management.

        **WARNING!**

        - You can use only one of the valid Query parameters: `active`, `status`, or
          `billId` in any call. If you use more than one of these Query parameters in
          the same call, then a 400 Bad Request is returned with an error message.

        Args:
          active: Boolean filter on whether to only retrieve active _(i.e. not
              completed/cancelled)_ StatementJobs.

              - TRUE - only active StatementJobs retrieved.
              - FALSE - all StatementJobs retrieved.

          bill_id: Filter Statement Jobs by billId

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              StatementJobs in a paginated list.

          page_size: Specifies the maximum number of StatementJobs to retrieve per page.

          status:
              Filter using the StatementJobs status. Possible values:

              - `PENDING`
              - `RUNNING`
              - `COMPLETE`
              - `CANCELLED`
              - `FAILED`

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
            f"/organizations/{org_id}/statementjobs",
            page=AsyncCursor[StatementJobResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "bill_id": bill_id,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    statement_job_list_params.StatementJobListParams,
                ),
            ),
            model=StatementJobResponse,
        )

    async def cancel(
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
    ) -> StatementJobResponse:
        """
        Cancel the StatementJob with the given UUID.

        Use this endpoint to halt the execution of a specific StatementJob identified by
        its UUID. This operation may be useful if you need to stop a StatementJob due to
        unforeseen issues or changes.

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
        return await self._post(
            f"/organizations/{org_id}/statementjobs/{id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobResponse,
        )

    async def create_batch(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        include_csv_format: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementJobCreateBatchResponse:
        """
        Create a batch of StatementJobs for multiple bills.

        Initiate the creation of multiple StatementJobs asynchronously for the list of
        bills with the given UUIDs:

        - The default format for generating Bill Statements is in JSON format and
          according to the Bill Statement Definition you've specified at either
          Organization level or Account level.
        - If you also want to generate the Statements in CSV format, use the
          `includeCsvFormat` request body parameter.
        - The response body provides a time-bound pre-signed URL, which you can use to
          download the JSON format Statement.
        - When you have generated a Statement for a Bill, you can also obtain a
          time-bound pre-signed download URL using either the
          [Retrieve Bill Statement in JSON Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillJsonStatement)
          and
          [Retrieve Bill Statement in CSV Format](https://www.m3ter.com/docs/api#tag/Bill/operation/GetBillCsvStatement)
          calls found in the [Bill](https://www.m3ter.com/docs/api#tag/Bill) section of
          this API Reference.

        **Notes:**

        - If the response to the Create StatementJob call shows the `statementJobStatus`
          as `PENDING` or `RUNNING`, you will not receive the pre-signed URL in the
          response. Wait a few minutes to allow the StatementJob to complete and then
          use the
          [Get StatmentJob](https://www.m3ter.com/docs/api#tag/StatementJob/operation/GetStatementJob)
          call in this section to obtain the pre-signed download URL for the generated
          Bill Statement.
        - When you have submitted a StatementJob and a Bill Statement has been
          generated, you can also download the Statement directly from a Bill Details
          page in the Console. See
          [Working with Bill Statements](https://www.m3ter.com/docs/guides/billing-and-usage-data/running-viewing-and-managing-bills/working-with-bill-statements)
          in our user Documentation.

        Args:
          bill_ids: The list of unique identifiers (UUIDs) of the bills associated with the
              StatementJob.

          include_csv_format: A Boolean value indicating whether the generated statement includes a CSV
              format.

              - TRUE - includes the statement in CSV format.
              - FALSE - no CSV format statement.

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
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._post(
            f"/organizations/{org_id}/statementjobs/batch",
            body=await async_maybe_transform(
                {
                    "bill_ids": bill_ids,
                    "include_csv_format": include_csv_format,
                    "version": version,
                },
                statement_job_create_batch_params.StatementJobCreateBatchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementJobCreateBatchResponse,
        )


class StatementJobsResourceWithRawResponse:
    def __init__(self, statement_jobs: StatementJobsResource) -> None:
        self._statement_jobs = statement_jobs

        self.create = to_raw_response_wrapper(
            statement_jobs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            statement_jobs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            statement_jobs.list,
        )
        self.cancel = to_raw_response_wrapper(
            statement_jobs.cancel,
        )
        self.create_batch = to_raw_response_wrapper(
            statement_jobs.create_batch,
        )


class AsyncStatementJobsResourceWithRawResponse:
    def __init__(self, statement_jobs: AsyncStatementJobsResource) -> None:
        self._statement_jobs = statement_jobs

        self.create = async_to_raw_response_wrapper(
            statement_jobs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            statement_jobs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            statement_jobs.list,
        )
        self.cancel = async_to_raw_response_wrapper(
            statement_jobs.cancel,
        )
        self.create_batch = async_to_raw_response_wrapper(
            statement_jobs.create_batch,
        )


class StatementJobsResourceWithStreamingResponse:
    def __init__(self, statement_jobs: StatementJobsResource) -> None:
        self._statement_jobs = statement_jobs

        self.create = to_streamed_response_wrapper(
            statement_jobs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            statement_jobs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            statement_jobs.list,
        )
        self.cancel = to_streamed_response_wrapper(
            statement_jobs.cancel,
        )
        self.create_batch = to_streamed_response_wrapper(
            statement_jobs.create_batch,
        )


class AsyncStatementJobsResourceWithStreamingResponse:
    def __init__(self, statement_jobs: AsyncStatementJobsResource) -> None:
        self._statement_jobs = statement_jobs

        self.create = async_to_streamed_response_wrapper(
            statement_jobs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            statement_jobs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            statement_jobs.list,
        )
        self.cancel = async_to_streamed_response_wrapper(
            statement_jobs.cancel,
        )
        self.create_batch = async_to_streamed_response_wrapper(
            statement_jobs.create_batch,
        )
