# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date

import httpx

from ..types import bill_config_update_params
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.bill_config_response import BillConfigResponse

__all__ = ["BillConfigResource", "AsyncBillConfigResource"]


class BillConfigResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BillConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return BillConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BillConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return BillConfigResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillConfigResponse:
        """
        Retrieve the Organization-wide BillConfig.

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
        return self._get(
            f"/organizations/{org_id}/billconfig",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillConfigResponse,
        )

    def update(
        self,
        *,
        org_id: str | None = None,
        bill_lock_date: Union[str, date] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillConfigResponse:
        """
        Update the Organization-wide BillConfig.

        You can use this endpoint to set a global lock date for **all** Bills - any Bill
        with a service period end date on or before the set date will be locked and
        cannot be updated or recalculated.

        Args:
          bill_lock_date: The global lock date when all Bills will be locked _(in ISO 8601 format)_.

              For example: `"2024-03-01"`.

          version:
              The version number:

              - Default value when newly created is one.
              - On Update, version is required and must match the existing version because a
                check is performed to ensure sequential versioning is preserved. Version is
                incremented by 1 and listed in the response

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return self._put(
            f"/organizations/{org_id}/billconfig",
            body=maybe_transform(
                {
                    "bill_lock_date": bill_lock_date,
                    "version": version,
                },
                bill_config_update_params.BillConfigUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillConfigResponse,
        )


class AsyncBillConfigResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBillConfigResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncBillConfigResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBillConfigResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncBillConfigResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillConfigResponse:
        """
        Retrieve the Organization-wide BillConfig.

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
        return await self._get(
            f"/organizations/{org_id}/billconfig",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillConfigResponse,
        )

    async def update(
        self,
        *,
        org_id: str | None = None,
        bill_lock_date: Union[str, date] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillConfigResponse:
        """
        Update the Organization-wide BillConfig.

        You can use this endpoint to set a global lock date for **all** Bills - any Bill
        with a service period end date on or before the set date will be locked and
        cannot be updated or recalculated.

        Args:
          bill_lock_date: The global lock date when all Bills will be locked _(in ISO 8601 format)_.

              For example: `"2024-03-01"`.

          version:
              The version number:

              - Default value when newly created is one.
              - On Update, version is required and must match the existing version because a
                check is performed to ensure sequential versioning is preserved. Version is
                incremented by 1 and listed in the response

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        return await self._put(
            f"/organizations/{org_id}/billconfig",
            body=await async_maybe_transform(
                {
                    "bill_lock_date": bill_lock_date,
                    "version": version,
                },
                bill_config_update_params.BillConfigUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillConfigResponse,
        )


class BillConfigResourceWithRawResponse:
    def __init__(self, bill_config: BillConfigResource) -> None:
        self._bill_config = bill_config

        self.retrieve = to_raw_response_wrapper(
            bill_config.retrieve,
        )
        self.update = to_raw_response_wrapper(
            bill_config.update,
        )


class AsyncBillConfigResourceWithRawResponse:
    def __init__(self, bill_config: AsyncBillConfigResource) -> None:
        self._bill_config = bill_config

        self.retrieve = async_to_raw_response_wrapper(
            bill_config.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            bill_config.update,
        )


class BillConfigResourceWithStreamingResponse:
    def __init__(self, bill_config: BillConfigResource) -> None:
        self._bill_config = bill_config

        self.retrieve = to_streamed_response_wrapper(
            bill_config.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            bill_config.update,
        )


class AsyncBillConfigResourceWithStreamingResponse:
    def __init__(self, bill_config: AsyncBillConfigResource) -> None:
        self._bill_config = bill_config

        self.retrieve = async_to_streamed_response_wrapper(
            bill_config.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            bill_config.update,
        )
