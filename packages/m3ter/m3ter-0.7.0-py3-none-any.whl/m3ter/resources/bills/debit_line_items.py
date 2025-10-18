# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ...types.bills import debit_line_item_list_params, debit_line_item_create_params, debit_line_item_update_params
from ..._base_client import AsyncPaginator, make_request_options
from ...types.bills.debit_line_item_response import DebitLineItemResponse

__all__ = ["DebitLineItemsResource", "AsyncDebitLineItemsResource"]


class DebitLineItemsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DebitLineItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DebitLineItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DebitLineItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return DebitLineItemsResourceWithStreamingResponse(self)

    def create(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        accounting_product_id: str,
        amount: float,
        description: str,
        product_id: str,
        referenced_bill_id: str,
        referenced_line_item_id: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        debit_reason_id: str | Omit = omit,
        line_item_type: Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ]
        | Omit = omit,
        reason_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Create a new Debit line item for the given bill.

        When creating Debit line items for Bills, use the Debit Reasons created for your
        Organization. See [DebitReason](https://www.m3ter.com/docs/api#tag/DebitReason).

        Args:
          accounting_product_id

          amount: The amount for the line item.

          description: The description for the line item.

          product_id: The UUID of the Product.

          referenced_bill_id: The UUID of the bill for the line item.

          referenced_line_item_id: The UUID of the line item.

          service_period_end_date: The service period end date in ISO-8601 format._(exclusive of the ending date)_.

          service_period_start_date: The service period start date in ISO-8601 format. _(inclusive of the starting
              date)_.

          debit_reason_id: The ID of the Debit Reason given for this debit line item.

          line_item_type

          reason_id: The UUID of the line item reason.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        return self._post(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems",
            body=maybe_transform(
                {
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "description": description,
                    "product_id": product_id,
                    "referenced_bill_id": referenced_bill_id,
                    "referenced_line_item_id": referenced_line_item_id,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "debit_reason_id": debit_reason_id,
                    "line_item_type": line_item_type,
                    "reason_id": reason_id,
                    "version": version,
                },
                debit_line_item_create_params.DebitLineItemCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Retrieve the Debit line item with the given UUID.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        accounting_product_id: str,
        amount: float,
        description: str,
        product_id: str,
        referenced_bill_id: str,
        referenced_line_item_id: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        debit_reason_id: str | Omit = omit,
        line_item_type: Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ]
        | Omit = omit,
        reason_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Update the Debit line item with the given UUID.

        Args:
          accounting_product_id

          amount: The amount for the line item.

          description: The description for the line item.

          product_id: The UUID of the Product.

          referenced_bill_id: The UUID of the bill for the line item.

          referenced_line_item_id: The UUID of the line item.

          service_period_end_date: The service period end date in ISO-8601 format._(exclusive of the ending date)_.

          service_period_start_date: The service period start date in ISO-8601 format. _(inclusive of the starting
              date)_.

          debit_reason_id: The ID of the Debit Reason given for this debit line item.

          line_item_type

          reason_id: The UUID of the line item reason.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            body=maybe_transform(
                {
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "description": description,
                    "product_id": product_id,
                    "referenced_bill_id": referenced_bill_id,
                    "referenced_line_item_id": referenced_line_item_id,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "debit_reason_id": debit_reason_id,
                    "line_item_type": line_item_type,
                    "reason_id": reason_id,
                    "version": version,
                },
                debit_line_item_update_params.DebitLineItemUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    def list(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[DebitLineItemResponse]:
        """
        List the Debit line items for the given bill.

        Args:
          next_token: `nextToken` for multi page retrievals.

          page_size: Number of line items to retrieve per page.

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
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems",
            page=SyncCursor[DebitLineItemResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    debit_line_item_list_params.DebitLineItemListParams,
                ),
            ),
            model=DebitLineItemResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Delete the Debit line item with the given UUID.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )


class AsyncDebitLineItemsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDebitLineItemsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDebitLineItemsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDebitLineItemsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncDebitLineItemsResourceWithStreamingResponse(self)

    async def create(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        accounting_product_id: str,
        amount: float,
        description: str,
        product_id: str,
        referenced_bill_id: str,
        referenced_line_item_id: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        debit_reason_id: str | Omit = omit,
        line_item_type: Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ]
        | Omit = omit,
        reason_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Create a new Debit line item for the given bill.

        When creating Debit line items for Bills, use the Debit Reasons created for your
        Organization. See [DebitReason](https://www.m3ter.com/docs/api#tag/DebitReason).

        Args:
          accounting_product_id

          amount: The amount for the line item.

          description: The description for the line item.

          product_id: The UUID of the Product.

          referenced_bill_id: The UUID of the bill for the line item.

          referenced_line_item_id: The UUID of the line item.

          service_period_end_date: The service period end date in ISO-8601 format._(exclusive of the ending date)_.

          service_period_start_date: The service period start date in ISO-8601 format. _(inclusive of the starting
              date)_.

          debit_reason_id: The ID of the Debit Reason given for this debit line item.

          line_item_type

          reason_id: The UUID of the line item reason.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        return await self._post(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems",
            body=await async_maybe_transform(
                {
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "description": description,
                    "product_id": product_id,
                    "referenced_bill_id": referenced_bill_id,
                    "referenced_line_item_id": referenced_line_item_id,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "debit_reason_id": debit_reason_id,
                    "line_item_type": line_item_type,
                    "reason_id": reason_id,
                    "version": version,
                },
                debit_line_item_create_params.DebitLineItemCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Retrieve the Debit line item with the given UUID.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        accounting_product_id: str,
        amount: float,
        description: str,
        product_id: str,
        referenced_bill_id: str,
        referenced_line_item_id: str,
        service_period_end_date: Union[str, datetime],
        service_period_start_date: Union[str, datetime],
        debit_reason_id: str | Omit = omit,
        line_item_type: Literal[
            "STANDING_CHARGE",
            "USAGE",
            "COUNTER_RUNNING_TOTAL_CHARGE",
            "COUNTER_ADJUSTMENT_DEBIT",
            "COUNTER_ADJUSTMENT_CREDIT",
            "USAGE_CREDIT",
            "MINIMUM_SPEND",
            "MINIMUM_SPEND_REFUND",
            "CREDIT_DEDUCTION",
            "MANUAL_ADJUSTMENT",
            "CREDIT_MEMO",
            "DEBIT_MEMO",
            "COMMITMENT_CONSUMED",
            "COMMITMENT_FEE",
            "OVERAGE_SURCHARGE",
            "OVERAGE_USAGE",
            "BALANCE_CONSUMED",
            "BALANCE_FEE",
        ]
        | Omit = omit,
        reason_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Update the Debit line item with the given UUID.

        Args:
          accounting_product_id

          amount: The amount for the line item.

          description: The description for the line item.

          product_id: The UUID of the Product.

          referenced_bill_id: The UUID of the bill for the line item.

          referenced_line_item_id: The UUID of the line item.

          service_period_end_date: The service period end date in ISO-8601 format._(exclusive of the ending date)_.

          service_period_start_date: The service period start date in ISO-8601 format. _(inclusive of the starting
              date)_.

          debit_reason_id: The ID of the Debit Reason given for this debit line item.

          line_item_type

          reason_id: The UUID of the line item reason.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            body=await async_maybe_transform(
                {
                    "accounting_product_id": accounting_product_id,
                    "amount": amount,
                    "description": description,
                    "product_id": product_id,
                    "referenced_bill_id": referenced_bill_id,
                    "referenced_line_item_id": referenced_line_item_id,
                    "service_period_end_date": service_period_end_date,
                    "service_period_start_date": service_period_start_date,
                    "debit_reason_id": debit_reason_id,
                    "line_item_type": line_item_type,
                    "reason_id": reason_id,
                    "version": version,
                },
                debit_line_item_update_params.DebitLineItemUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )

    def list(
        self,
        bill_id: str,
        *,
        org_id: str | None = None,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[DebitLineItemResponse, AsyncCursor[DebitLineItemResponse]]:
        """
        List the Debit line items for the given bill.

        Args:
          next_token: `nextToken` for multi page retrievals.

          page_size: Number of line items to retrieve per page.

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
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems",
            page=AsyncCursor[DebitLineItemResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    debit_line_item_list_params.DebitLineItemListParams,
                ),
            ),
            model=DebitLineItemResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DebitLineItemResponse:
        """
        Delete the Debit line item with the given UUID.

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
        if not bill_id:
            raise ValueError(f"Expected a non-empty value for `bill_id` but received {bill_id!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/bills/{bill_id}/debitlineitems/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitLineItemResponse,
        )


class DebitLineItemsResourceWithRawResponse:
    def __init__(self, debit_line_items: DebitLineItemsResource) -> None:
        self._debit_line_items = debit_line_items

        self.create = to_raw_response_wrapper(
            debit_line_items.create,
        )
        self.retrieve = to_raw_response_wrapper(
            debit_line_items.retrieve,
        )
        self.update = to_raw_response_wrapper(
            debit_line_items.update,
        )
        self.list = to_raw_response_wrapper(
            debit_line_items.list,
        )
        self.delete = to_raw_response_wrapper(
            debit_line_items.delete,
        )


class AsyncDebitLineItemsResourceWithRawResponse:
    def __init__(self, debit_line_items: AsyncDebitLineItemsResource) -> None:
        self._debit_line_items = debit_line_items

        self.create = async_to_raw_response_wrapper(
            debit_line_items.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            debit_line_items.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            debit_line_items.update,
        )
        self.list = async_to_raw_response_wrapper(
            debit_line_items.list,
        )
        self.delete = async_to_raw_response_wrapper(
            debit_line_items.delete,
        )


class DebitLineItemsResourceWithStreamingResponse:
    def __init__(self, debit_line_items: DebitLineItemsResource) -> None:
        self._debit_line_items = debit_line_items

        self.create = to_streamed_response_wrapper(
            debit_line_items.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            debit_line_items.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            debit_line_items.update,
        )
        self.list = to_streamed_response_wrapper(
            debit_line_items.list,
        )
        self.delete = to_streamed_response_wrapper(
            debit_line_items.delete,
        )


class AsyncDebitLineItemsResourceWithStreamingResponse:
    def __init__(self, debit_line_items: AsyncDebitLineItemsResource) -> None:
        self._debit_line_items = debit_line_items

        self.create = async_to_streamed_response_wrapper(
            debit_line_items.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            debit_line_items.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            debit_line_items.update,
        )
        self.list = async_to_streamed_response_wrapper(
            debit_line_items.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            debit_line_items.delete,
        )
