# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import counter_list_params, counter_create_params, counter_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..pagination import SyncCursor, AsyncCursor
from .._base_client import AsyncPaginator, make_request_options
from ..types.counter_response import CounterResponse

__all__ = ["CountersResource", "AsyncCountersResource"]


class CountersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CountersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CountersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CountersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CountersResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        unit: str,
        code: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterResponse:
        """
        Create a new Counter.

        Args:
          name: Descriptive name for the Counter.

          unit: User defined label for units shown on Bill line items, and indicating to your
              customers what they are being charged for.

          code: Code for the Counter. A unique short code to identify the Counter.

          product_id: UUID of the product the Counter belongs to. _(Optional)_ - if left blank, the
              Counter is Global. A Global Counter can be used to price Plans or Plan Templates
              belonging to any Product.

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
            f"/organizations/{org_id}/counters",
            body=maybe_transform(
                {
                    "name": name,
                    "unit": unit,
                    "code": code,
                    "product_id": product_id,
                    "version": version,
                },
                counter_create_params.CounterCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
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
    ) -> CounterResponse:
        """
        Retrieve a Counter for the given UUID.

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
            f"/organizations/{org_id}/counters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        unit: str,
        code: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterResponse:
        """
        Update Counter for the given UUID.

        Args:
          name: Descriptive name for the Counter.

          unit: User defined label for units shown on Bill line items, and indicating to your
              customers what they are being charged for.

          code: Code for the Counter. A unique short code to identify the Counter.

          product_id: UUID of the product the Counter belongs to. _(Optional)_ - if left blank, the
              Counter is Global. A Global Counter can be used to price Plans or Plan Templates
              belonging to any Product.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/counters/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "unit": unit,
                    "code": code,
                    "product_id": product_id,
                    "version": version,
                },
                counter_update_params.CounterUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        product_id: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[CounterResponse]:
        """
        Retrieve a list of Counter entities that can be filtered by Product, Counter ID,
        or Codes.

        Args:
          codes: List of Counter codes to retrieve. These are unique short codes to identify each
              Counter.

          ids: List of Counter IDs to retrieve.

          next_token: NextToken for multi page retrievals.

          page_size: Number of Counters to retrieve per page

          product_id: List of Products UUIDs to retrieve Counters for.

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
            f"/organizations/{org_id}/counters",
            page=SyncCursor[CounterResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    counter_list_params.CounterListParams,
                ),
            ),
            model=CounterResponse,
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
    ) -> CounterResponse:
        """
        Delete a Counter for the given UUID.

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
        return self._delete(
            f"/organizations/{org_id}/counters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )


class AsyncCountersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCountersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCountersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCountersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCountersResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        unit: str,
        code: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterResponse:
        """
        Create a new Counter.

        Args:
          name: Descriptive name for the Counter.

          unit: User defined label for units shown on Bill line items, and indicating to your
              customers what they are being charged for.

          code: Code for the Counter. A unique short code to identify the Counter.

          product_id: UUID of the product the Counter belongs to. _(Optional)_ - if left blank, the
              Counter is Global. A Global Counter can be used to price Plans or Plan Templates
              belonging to any Product.

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
            f"/organizations/{org_id}/counters",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "unit": unit,
                    "code": code,
                    "product_id": product_id,
                    "version": version,
                },
                counter_create_params.CounterCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
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
    ) -> CounterResponse:
        """
        Retrieve a Counter for the given UUID.

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
            f"/organizations/{org_id}/counters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        unit: str,
        code: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterResponse:
        """
        Update Counter for the given UUID.

        Args:
          name: Descriptive name for the Counter.

          unit: User defined label for units shown on Bill line items, and indicating to your
              customers what they are being charged for.

          code: Code for the Counter. A unique short code to identify the Counter.

          product_id: UUID of the product the Counter belongs to. _(Optional)_ - if left blank, the
              Counter is Global. A Global Counter can be used to price Plans or Plan Templates
              belonging to any Product.

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
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/counters/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "unit": unit,
                    "code": code,
                    "product_id": product_id,
                    "version": version,
                },
                counter_update_params.CounterUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        product_id: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[CounterResponse, AsyncCursor[CounterResponse]]:
        """
        Retrieve a list of Counter entities that can be filtered by Product, Counter ID,
        or Codes.

        Args:
          codes: List of Counter codes to retrieve. These are unique short codes to identify each
              Counter.

          ids: List of Counter IDs to retrieve.

          next_token: NextToken for multi page retrievals.

          page_size: Number of Counters to retrieve per page

          product_id: List of Products UUIDs to retrieve Counters for.

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
            f"/organizations/{org_id}/counters",
            page=AsyncCursor[CounterResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    counter_list_params.CounterListParams,
                ),
            ),
            model=CounterResponse,
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
    ) -> CounterResponse:
        """
        Delete a Counter for the given UUID.

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
        return await self._delete(
            f"/organizations/{org_id}/counters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterResponse,
        )


class CountersResourceWithRawResponse:
    def __init__(self, counters: CountersResource) -> None:
        self._counters = counters

        self.create = to_raw_response_wrapper(
            counters.create,
        )
        self.retrieve = to_raw_response_wrapper(
            counters.retrieve,
        )
        self.update = to_raw_response_wrapper(
            counters.update,
        )
        self.list = to_raw_response_wrapper(
            counters.list,
        )
        self.delete = to_raw_response_wrapper(
            counters.delete,
        )


class AsyncCountersResourceWithRawResponse:
    def __init__(self, counters: AsyncCountersResource) -> None:
        self._counters = counters

        self.create = async_to_raw_response_wrapper(
            counters.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            counters.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            counters.update,
        )
        self.list = async_to_raw_response_wrapper(
            counters.list,
        )
        self.delete = async_to_raw_response_wrapper(
            counters.delete,
        )


class CountersResourceWithStreamingResponse:
    def __init__(self, counters: CountersResource) -> None:
        self._counters = counters

        self.create = to_streamed_response_wrapper(
            counters.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            counters.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            counters.update,
        )
        self.list = to_streamed_response_wrapper(
            counters.list,
        )
        self.delete = to_streamed_response_wrapper(
            counters.delete,
        )


class AsyncCountersResourceWithStreamingResponse:
    def __init__(self, counters: AsyncCountersResource) -> None:
        self._counters = counters

        self.create = async_to_streamed_response_wrapper(
            counters.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            counters.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            counters.update,
        )
        self.list = async_to_streamed_response_wrapper(
            counters.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            counters.delete,
        )
