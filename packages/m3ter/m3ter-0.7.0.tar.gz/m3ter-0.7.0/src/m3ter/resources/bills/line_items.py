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
from ...types.bills import line_item_list_params, line_item_retrieve_params
from ..._base_client import AsyncPaginator, make_request_options
from ...types.bills.line_item_response import LineItemResponse

__all__ = ["LineItemsResource", "AsyncLineItemsResource"]


class LineItemsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LineItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return LineItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LineItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return LineItemsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LineItemResponse:
        """
        Retrieves a specific line item within a Bill.

        This endpoint retrieves the line item given by its unique identifier (UUID) from
        a specific Bill.

        Args:
          additional: Comma separated list of additional fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/bills/{bill_id}/lineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"additional": additional}, line_item_retrieve_params.LineItemRetrieveParams),
            ),
            cast_to=LineItemResponse,
        )

    def list(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[LineItemResponse]:
        """
        Lists all the line items for a specific Bill.

        This endpoint retrieves a list of line items for the given Bill within the
        specified Organization. The list can also be paginated for easier management.
        The line items returned in the list include individual charges, discounts, or
        adjustments within a Bill.

        Args:
          additional: Comma separated list of additional fields.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              line items in a paginated list.

          page_size: Specifies the maximum number of line items to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/bills/{bill_id}/lineitems",
            page=SyncCursor[LineItemResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "additional": additional,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    line_item_list_params.LineItemListParams,
                ),
            ),
            model=LineItemResponse,
        )


class AsyncLineItemsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLineItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncLineItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLineItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncLineItemsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LineItemResponse:
        """
        Retrieves a specific line item within a Bill.

        This endpoint retrieves the line item given by its unique identifier (UUID) from
        a specific Bill.

        Args:
          additional: Comma separated list of additional fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/bills/{bill_id}/lineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"additional": additional}, line_item_retrieve_params.LineItemRetrieveParams
                ),
            ),
            cast_to=LineItemResponse,
        )

    def list(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[LineItemResponse, AsyncCursor[LineItemResponse]]:
        """
        Lists all the line items for a specific Bill.

        This endpoint retrieves a list of line items for the given Bill within the
        specified Organization. The list can also be paginated for easier management.
        The line items returned in the list include individual charges, discounts, or
        adjustments within a Bill.

        Args:
          additional: Comma separated list of additional fields.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              line items in a paginated list.

          page_size: Specifies the maximum number of line items to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/bills/{bill_id}/lineitems",
            page=AsyncCursor[LineItemResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "additional": additional,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    line_item_list_params.LineItemListParams,
                ),
            ),
            model=LineItemResponse,
        )


class LineItemsResourceWithRawResponse:
    def __init__(self, line_items: LineItemsResource) -> None:
        self._line_items = line_items

        self.retrieve = to_raw_response_wrapper(
            line_items.retrieve,
        )
        self.list = to_raw_response_wrapper(
            line_items.list,
        )


class AsyncLineItemsResourceWithRawResponse:
    def __init__(self, line_items: AsyncLineItemsResource) -> None:
        self._line_items = line_items

        self.retrieve = async_to_raw_response_wrapper(
            line_items.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            line_items.list,
        )


class LineItemsResourceWithStreamingResponse:
    def __init__(self, line_items: LineItemsResource) -> None:
        self._line_items = line_items

        self.retrieve = to_streamed_response_wrapper(
            line_items.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            line_items.list,
        )


class AsyncLineItemsResourceWithStreamingResponse:
    def __init__(self, line_items: AsyncLineItemsResource) -> None:
        self._line_items = line_items

        self.retrieve = async_to_streamed_response_wrapper(
            line_items.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            line_items.list,
        )
