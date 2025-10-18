# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional

import httpx

from ..types import counter_adjustment_list_params, counter_adjustment_create_params, counter_adjustment_update_params
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
from ..pagination import SyncCursor, AsyncCursor
from .._base_client import AsyncPaginator, make_request_options
from ..types.counter_adjustment_response import CounterAdjustmentResponse

__all__ = ["CounterAdjustmentsResource", "AsyncCounterAdjustmentsResource"]


class CounterAdjustmentsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CounterAdjustmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CounterAdjustmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CounterAdjustmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CounterAdjustmentsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        counter_id: str,
        date: str,
        value: int,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterAdjustmentResponse:
        """
        Create a new CounterAdjustment for an Account using a Counter.

        **Notes:**

        - Use the new absolute value for the Counter for the selected date - if it was
          15 and has increased to 20, enter 20; if it was 15 and has decreased to 10,
          enter 10. _Do not enter_ the plus or minus value relative to the previous
          Counter value on the Account.
        - CounterAdjustments on Accounts are supported down to a _specific day_ of
          granularity - you cannot create more than one CounterAdjustment for any given
          day using the same Counter and you'll receive an error if you try to do this.

        Args:
          account_id: The Account ID the CounterAdjustment is created for.

          counter_id: The ID of the Counter used for the CounterAdjustment on the Account.

          date: The date the CounterAdjustment is created for the Account _(in ISO-8601 date
              format)_.

              **Note:** CounterAdjustments on Accounts are supported down to a _specific day_
              of granularity - you cannot create more than one CounterAdjustment for any given
              day using the same Counter and you'll receive an error if you try to do this.

          value: Integer Value of the Counter used for the CounterAdjustment.

              **Note:** Use the new absolute value for the Counter for the selected date - if
              it was 15 and has increased to 20, enter 20; if it was 15 and has decreased to
              10, enter 10. _Do not enter_ the plus or minus value relative to the previous
              Counter value on the Account.

          purchase_order_number: Purchase Order Number for the Counter Adjustment. _(Optional)_

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
            f"/organizations/{org_id}/counteradjustments",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": date,
                    "value": value,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                counter_adjustment_create_params.CounterAdjustmentCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
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
    ) -> CounterAdjustmentResponse:
        """
        Retrieve a CounterAdjustment for the given UUID.

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        counter_id: str,
        date: str,
        value: int,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterAdjustmentResponse:
        """
        Update a CounterAdjustment for an Account.

        Args:
          account_id: The Account ID the CounterAdjustment is created for.

          counter_id: The ID of the Counter used for the CounterAdjustment on the Account.

          date: The date the CounterAdjustment is created for the Account _(in ISO-8601 date
              format)_.

              **Note:** CounterAdjustments on Accounts are supported down to a _specific day_
              of granularity - you cannot create more than one CounterAdjustment for any given
              day using the same Counter and you'll receive an error if you try to do this.

          value: Integer Value of the Counter used for the CounterAdjustment.

              **Note:** Use the new absolute value for the Counter for the selected date - if
              it was 15 and has increased to 20, enter 20; if it was 15 and has decreased to
              10, enter 10. _Do not enter_ the plus or minus value relative to the previous
              Counter value on the Account.

          purchase_order_number: Purchase Order Number for the Counter Adjustment. _(Optional)_

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": date,
                    "value": value,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                counter_adjustment_update_params.CounterAdjustmentUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        counter_id: str | Omit = omit,
        date: str | Omit = omit,
        date_end: Optional[str] | Omit = omit,
        date_start: Optional[str] | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        sort_order: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[CounterAdjustmentResponse]:
        """
        Retrieve a list of CounterAdjustments created for Accounts in your Organization.
        You can filter the list returned by date, Account ID, or Counter ID.

        **CONSTRAINTS:**

        - The `counterId` query parameter is always required when calling this endpoint,
          used either as a single query parameter or in combination with any of the
          other query parameters.
        - If you want to use the `date`, `dateStart`, or `dateEnd` query parameters, you
          must also use the `accountId` query parameter.

        Args:
          account_id: List CounterAdjustment items for the Account UUID.

          counter_id: List CounterAdjustment items for the Counter UUID.

          date: List CounterAdjustment items for the given date.

          end_date_end: Only include CounterAdjustments with end dates earlier than this date.

          end_date_start: Only include CounterAdjustments with end dates equal to or later than this date.

          next_token: nextToken for multi page retrievals.

          page_size: Number of CounterAdjustments to retrieve per page

          sort_order: Sort order for the results

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
            f"/organizations/{org_id}/counteradjustments",
            page=SyncCursor[CounterAdjustmentResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "counter_id": counter_id,
                        "date": date,
                        "date_end": date_end,
                        "date_start": date_start,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "next_token": next_token,
                        "page_size": page_size,
                        "sort_order": sort_order,
                    },
                    counter_adjustment_list_params.CounterAdjustmentListParams,
                ),
            ),
            model=CounterAdjustmentResponse,
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
    ) -> CounterAdjustmentResponse:
        """
        Delete a CounterAdjustment for the given UUID.

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )


class AsyncCounterAdjustmentsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCounterAdjustmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCounterAdjustmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCounterAdjustmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCounterAdjustmentsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        counter_id: str,
        date: str,
        value: int,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterAdjustmentResponse:
        """
        Create a new CounterAdjustment for an Account using a Counter.

        **Notes:**

        - Use the new absolute value for the Counter for the selected date - if it was
          15 and has increased to 20, enter 20; if it was 15 and has decreased to 10,
          enter 10. _Do not enter_ the plus or minus value relative to the previous
          Counter value on the Account.
        - CounterAdjustments on Accounts are supported down to a _specific day_ of
          granularity - you cannot create more than one CounterAdjustment for any given
          day using the same Counter and you'll receive an error if you try to do this.

        Args:
          account_id: The Account ID the CounterAdjustment is created for.

          counter_id: The ID of the Counter used for the CounterAdjustment on the Account.

          date: The date the CounterAdjustment is created for the Account _(in ISO-8601 date
              format)_.

              **Note:** CounterAdjustments on Accounts are supported down to a _specific day_
              of granularity - you cannot create more than one CounterAdjustment for any given
              day using the same Counter and you'll receive an error if you try to do this.

          value: Integer Value of the Counter used for the CounterAdjustment.

              **Note:** Use the new absolute value for the Counter for the selected date - if
              it was 15 and has increased to 20, enter 20; if it was 15 and has decreased to
              10, enter 10. _Do not enter_ the plus or minus value relative to the previous
              Counter value on the Account.

          purchase_order_number: Purchase Order Number for the Counter Adjustment. _(Optional)_

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
            f"/organizations/{org_id}/counteradjustments",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": date,
                    "value": value,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                counter_adjustment_create_params.CounterAdjustmentCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
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
    ) -> CounterAdjustmentResponse:
        """
        Retrieve a CounterAdjustment for the given UUID.

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        counter_id: str,
        date: str,
        value: int,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterAdjustmentResponse:
        """
        Update a CounterAdjustment for an Account.

        Args:
          account_id: The Account ID the CounterAdjustment is created for.

          counter_id: The ID of the Counter used for the CounterAdjustment on the Account.

          date: The date the CounterAdjustment is created for the Account _(in ISO-8601 date
              format)_.

              **Note:** CounterAdjustments on Accounts are supported down to a _specific day_
              of granularity - you cannot create more than one CounterAdjustment for any given
              day using the same Counter and you'll receive an error if you try to do this.

          value: Integer Value of the Counter used for the CounterAdjustment.

              **Note:** Use the new absolute value for the Counter for the selected date - if
              it was 15 and has increased to 20, enter 20; if it was 15 and has decreased to
              10, enter 10. _Do not enter_ the plus or minus value relative to the previous
              Counter value on the Account.

          purchase_order_number: Purchase Order Number for the Counter Adjustment. _(Optional)_

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "counter_id": counter_id,
                    "date": date,
                    "value": value,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                counter_adjustment_update_params.CounterAdjustmentUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        counter_id: str | Omit = omit,
        date: str | Omit = omit,
        date_end: Optional[str] | Omit = omit,
        date_start: Optional[str] | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        sort_order: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[CounterAdjustmentResponse, AsyncCursor[CounterAdjustmentResponse]]:
        """
        Retrieve a list of CounterAdjustments created for Accounts in your Organization.
        You can filter the list returned by date, Account ID, or Counter ID.

        **CONSTRAINTS:**

        - The `counterId` query parameter is always required when calling this endpoint,
          used either as a single query parameter or in combination with any of the
          other query parameters.
        - If you want to use the `date`, `dateStart`, or `dateEnd` query parameters, you
          must also use the `accountId` query parameter.

        Args:
          account_id: List CounterAdjustment items for the Account UUID.

          counter_id: List CounterAdjustment items for the Counter UUID.

          date: List CounterAdjustment items for the given date.

          end_date_end: Only include CounterAdjustments with end dates earlier than this date.

          end_date_start: Only include CounterAdjustments with end dates equal to or later than this date.

          next_token: nextToken for multi page retrievals.

          page_size: Number of CounterAdjustments to retrieve per page

          sort_order: Sort order for the results

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
            f"/organizations/{org_id}/counteradjustments",
            page=AsyncCursor[CounterAdjustmentResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "counter_id": counter_id,
                        "date": date,
                        "date_end": date_end,
                        "date_start": date_start,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "next_token": next_token,
                        "page_size": page_size,
                        "sort_order": sort_order,
                    },
                    counter_adjustment_list_params.CounterAdjustmentListParams,
                ),
            ),
            model=CounterAdjustmentResponse,
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
    ) -> CounterAdjustmentResponse:
        """
        Delete a CounterAdjustment for the given UUID.

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
            f"/organizations/{org_id}/counteradjustments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterAdjustmentResponse,
        )


class CounterAdjustmentsResourceWithRawResponse:
    def __init__(self, counter_adjustments: CounterAdjustmentsResource) -> None:
        self._counter_adjustments = counter_adjustments

        self.create = to_raw_response_wrapper(
            counter_adjustments.create,
        )
        self.retrieve = to_raw_response_wrapper(
            counter_adjustments.retrieve,
        )
        self.update = to_raw_response_wrapper(
            counter_adjustments.update,
        )
        self.list = to_raw_response_wrapper(
            counter_adjustments.list,
        )
        self.delete = to_raw_response_wrapper(
            counter_adjustments.delete,
        )


class AsyncCounterAdjustmentsResourceWithRawResponse:
    def __init__(self, counter_adjustments: AsyncCounterAdjustmentsResource) -> None:
        self._counter_adjustments = counter_adjustments

        self.create = async_to_raw_response_wrapper(
            counter_adjustments.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            counter_adjustments.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            counter_adjustments.update,
        )
        self.list = async_to_raw_response_wrapper(
            counter_adjustments.list,
        )
        self.delete = async_to_raw_response_wrapper(
            counter_adjustments.delete,
        )


class CounterAdjustmentsResourceWithStreamingResponse:
    def __init__(self, counter_adjustments: CounterAdjustmentsResource) -> None:
        self._counter_adjustments = counter_adjustments

        self.create = to_streamed_response_wrapper(
            counter_adjustments.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            counter_adjustments.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            counter_adjustments.update,
        )
        self.list = to_streamed_response_wrapper(
            counter_adjustments.list,
        )
        self.delete = to_streamed_response_wrapper(
            counter_adjustments.delete,
        )


class AsyncCounterAdjustmentsResourceWithStreamingResponse:
    def __init__(self, counter_adjustments: AsyncCounterAdjustmentsResource) -> None:
        self._counter_adjustments = counter_adjustments

        self.create = async_to_streamed_response_wrapper(
            counter_adjustments.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            counter_adjustments.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            counter_adjustments.update,
        )
        self.list = async_to_streamed_response_wrapper(
            counter_adjustments.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            counter_adjustments.delete,
        )
