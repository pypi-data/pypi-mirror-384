# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from .statement_jobs import (
    StatementJobsResource,
    AsyncStatementJobsResource,
    StatementJobsResourceWithRawResponse,
    AsyncStatementJobsResourceWithRawResponse,
    StatementJobsResourceWithStreamingResponse,
    AsyncStatementJobsResourceWithStreamingResponse,
)
from .statement_definitions import (
    StatementDefinitionsResource,
    AsyncStatementDefinitionsResource,
    StatementDefinitionsResourceWithRawResponse,
    AsyncStatementDefinitionsResourceWithRawResponse,
    StatementDefinitionsResourceWithStreamingResponse,
    AsyncStatementDefinitionsResourceWithStreamingResponse,
)
from ...types.object_url_response import ObjectURLResponse

__all__ = ["StatementsResource", "AsyncStatementsResource"]


class StatementsResource(SyncAPIResource):
    @cached_property
    def statement_jobs(self) -> StatementJobsResource:
        return StatementJobsResource(self._client)

    @cached_property
    def statement_definitions(self) -> StatementDefinitionsResource:
        return StatementDefinitionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> StatementsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return StatementsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StatementsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return StatementsResourceWithStreamingResponse(self)

    def create_csv(
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
    ) -> ObjectURLResponse:
        """
        Generate a specific Bill Statement for the provided Bill UUID in CSV format.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response to this call returns a pre-signed `downloadUrl`, which you then use
        with a `GET` call to obtain the Bill statement in CSV format.

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
            f"/organizations/{org_id}/bills/{id}/statement/csv",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )

    def get_csv(
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
    ) -> ObjectURLResponse:
        """
        Retrieve a specific Bill Statement for the given Bill UUID in CSV format.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response includes a pre-signed `downloadUrl`, which must be used with a
        separate `GET` call to download the actual Bill Statement. This ensures secure
        access to the requested information.

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
            f"/organizations/{org_id}/bills/{id}/statement/csv",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )

    def get_json(
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
    ) -> ObjectURLResponse:
        """
        Retrieve a Bill Statement in JSON format for a given Bill ID.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response to this call returns a pre-signed `downloadUrl`, which you use with
        a `GET` call to obtain the Bill Statement.

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
            f"/organizations/{org_id}/bills/{id}/statement/json",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )


class AsyncStatementsResource(AsyncAPIResource):
    @cached_property
    def statement_jobs(self) -> AsyncStatementJobsResource:
        return AsyncStatementJobsResource(self._client)

    @cached_property
    def statement_definitions(self) -> AsyncStatementDefinitionsResource:
        return AsyncStatementDefinitionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncStatementsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStatementsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStatementsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncStatementsResourceWithStreamingResponse(self)

    async def create_csv(
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
    ) -> ObjectURLResponse:
        """
        Generate a specific Bill Statement for the provided Bill UUID in CSV format.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response to this call returns a pre-signed `downloadUrl`, which you then use
        with a `GET` call to obtain the Bill statement in CSV format.

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
            f"/organizations/{org_id}/bills/{id}/statement/csv",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )

    async def get_csv(
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
    ) -> ObjectURLResponse:
        """
        Retrieve a specific Bill Statement for the given Bill UUID in CSV format.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response includes a pre-signed `downloadUrl`, which must be used with a
        separate `GET` call to download the actual Bill Statement. This ensures secure
        access to the requested information.

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
            f"/organizations/{org_id}/bills/{id}/statement/csv",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )

    async def get_json(
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
    ) -> ObjectURLResponse:
        """
        Retrieve a Bill Statement in JSON format for a given Bill ID.

        Bill Statements are backing sheets to the invoices sent to your customers. Bill
        Statements provide a breakdown of the usage responsible for the usage charge
        line items shown on invoices.

        The response to this call returns a pre-signed `downloadUrl`, which you use with
        a `GET` call to obtain the Bill Statement.

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
            f"/organizations/{org_id}/bills/{id}/statement/json",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ObjectURLResponse,
        )


class StatementsResourceWithRawResponse:
    def __init__(self, statements: StatementsResource) -> None:
        self._statements = statements

        self.create_csv = to_raw_response_wrapper(
            statements.create_csv,
        )
        self.get_csv = to_raw_response_wrapper(
            statements.get_csv,
        )
        self.get_json = to_raw_response_wrapper(
            statements.get_json,
        )

    @cached_property
    def statement_jobs(self) -> StatementJobsResourceWithRawResponse:
        return StatementJobsResourceWithRawResponse(self._statements.statement_jobs)

    @cached_property
    def statement_definitions(self) -> StatementDefinitionsResourceWithRawResponse:
        return StatementDefinitionsResourceWithRawResponse(self._statements.statement_definitions)


class AsyncStatementsResourceWithRawResponse:
    def __init__(self, statements: AsyncStatementsResource) -> None:
        self._statements = statements

        self.create_csv = async_to_raw_response_wrapper(
            statements.create_csv,
        )
        self.get_csv = async_to_raw_response_wrapper(
            statements.get_csv,
        )
        self.get_json = async_to_raw_response_wrapper(
            statements.get_json,
        )

    @cached_property
    def statement_jobs(self) -> AsyncStatementJobsResourceWithRawResponse:
        return AsyncStatementJobsResourceWithRawResponse(self._statements.statement_jobs)

    @cached_property
    def statement_definitions(self) -> AsyncStatementDefinitionsResourceWithRawResponse:
        return AsyncStatementDefinitionsResourceWithRawResponse(self._statements.statement_definitions)


class StatementsResourceWithStreamingResponse:
    def __init__(self, statements: StatementsResource) -> None:
        self._statements = statements

        self.create_csv = to_streamed_response_wrapper(
            statements.create_csv,
        )
        self.get_csv = to_streamed_response_wrapper(
            statements.get_csv,
        )
        self.get_json = to_streamed_response_wrapper(
            statements.get_json,
        )

    @cached_property
    def statement_jobs(self) -> StatementJobsResourceWithStreamingResponse:
        return StatementJobsResourceWithStreamingResponse(self._statements.statement_jobs)

    @cached_property
    def statement_definitions(self) -> StatementDefinitionsResourceWithStreamingResponse:
        return StatementDefinitionsResourceWithStreamingResponse(self._statements.statement_definitions)


class AsyncStatementsResourceWithStreamingResponse:
    def __init__(self, statements: AsyncStatementsResource) -> None:
        self._statements = statements

        self.create_csv = async_to_streamed_response_wrapper(
            statements.create_csv,
        )
        self.get_csv = async_to_streamed_response_wrapper(
            statements.get_csv,
        )
        self.get_json = async_to_streamed_response_wrapper(
            statements.get_json,
        )

    @cached_property
    def statement_jobs(self) -> AsyncStatementJobsResourceWithStreamingResponse:
        return AsyncStatementJobsResourceWithStreamingResponse(self._statements.statement_jobs)

    @cached_property
    def statement_definitions(self) -> AsyncStatementDefinitionsResourceWithStreamingResponse:
        return AsyncStatementDefinitionsResourceWithStreamingResponse(self._statements.statement_definitions)
