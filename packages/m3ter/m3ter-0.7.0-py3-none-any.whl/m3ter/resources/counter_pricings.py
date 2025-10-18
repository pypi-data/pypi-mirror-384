# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime

import httpx

from ..types import counter_pricing_list_params, counter_pricing_create_params, counter_pricing_update_params
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
from ..types.counter_pricing_response import CounterPricingResponse
from ..types.shared_params.pricing_band import PricingBand

__all__ = ["CounterPricingsResource", "AsyncCounterPricingsResource"]


class CounterPricingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CounterPricingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CounterPricingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CounterPricingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CounterPricingsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        counter_id: str,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        pro_rate_adjustment_credit: bool | Omit = omit,
        pro_rate_adjustment_debit: bool | Omit = omit,
        pro_rate_running_total: bool | Omit = omit,
        running_total_bill_in_advance: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterPricingResponse:
        """
        Create a new CounterPricing.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          counter_id: UUID of the Counter used to create the pricing.

          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          code: Unique short code for the Pricing.

          cumulative: Controls whether or not charge rates under a set of pricing bands configured for
              a Pricing are applied according to each separate band or at the highest band
              reached.

              _(Optional)_. The default value is **FALSE**.

              - When TRUE, at billing charge rates are applied according to each separate
                band.

              - When FALSE, at billing charge rates are applied according to highest band
                reached.

              **NOTE:** Use the `cumulative` parameter to create the type of Pricing you
              require. For example, for Tiered Pricing set to **TRUE**; for Volume Pricing,
              set to **FALSE**.

          description: Displayed on Bill line items.

          end_date: The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
              the Plan or Plan Template.

              _(Optional)_ If not specified, the Pricing remains active indefinitely.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          pro_rate_adjustment_credit: The default value is **TRUE**.

              - When TRUE, counter adjustment credits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment credits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_adjustment_debit: The default value is **TRUE**.

              - When TRUE, counter adjustment debits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment debits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_running_total: The default value is **TRUE**.

              - When TRUE, counter running total charges are prorated and are billed according
                to the number of days in billing period.

              - When FALSE, counter running total charges are not prorated and are billed for
                the entire billing period.

              _(Optional)_.

          running_total_bill_in_advance: The default value is **TRUE**.

              - When TRUE, running totals are billed at the start of each billing period.

              - When FALSE, running totals are billed at the end of each billing period.

              _(Optional)_.

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
            f"/organizations/{org_id}/counterpricings",
            body=maybe_transform(
                {
                    "counter_id": counter_id,
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "pro_rate_adjustment_credit": pro_rate_adjustment_credit,
                    "pro_rate_adjustment_debit": pro_rate_adjustment_debit,
                    "pro_rate_running_total": pro_rate_running_total,
                    "running_total_bill_in_advance": running_total_bill_in_advance,
                    "version": version,
                },
                counter_pricing_create_params.CounterPricingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
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
    ) -> CounterPricingResponse:
        """
        Retrieve a CounterPricing for the given UUID.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        counter_id: str,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        pro_rate_adjustment_credit: bool | Omit = omit,
        pro_rate_adjustment_debit: bool | Omit = omit,
        pro_rate_running_total: bool | Omit = omit,
        running_total_bill_in_advance: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterPricingResponse:
        """
        Update CounterPricing for the given UUID.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          counter_id: UUID of the Counter used to create the pricing.

          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          code: Unique short code for the Pricing.

          cumulative: Controls whether or not charge rates under a set of pricing bands configured for
              a Pricing are applied according to each separate band or at the highest band
              reached.

              _(Optional)_. The default value is **FALSE**.

              - When TRUE, at billing charge rates are applied according to each separate
                band.

              - When FALSE, at billing charge rates are applied according to highest band
                reached.

              **NOTE:** Use the `cumulative` parameter to create the type of Pricing you
              require. For example, for Tiered Pricing set to **TRUE**; for Volume Pricing,
              set to **FALSE**.

          description: Displayed on Bill line items.

          end_date: The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
              the Plan or Plan Template.

              _(Optional)_ If not specified, the Pricing remains active indefinitely.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          pro_rate_adjustment_credit: The default value is **TRUE**.

              - When TRUE, counter adjustment credits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment credits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_adjustment_debit: The default value is **TRUE**.

              - When TRUE, counter adjustment debits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment debits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_running_total: The default value is **TRUE**.

              - When TRUE, counter running total charges are prorated and are billed according
                to the number of days in billing period.

              - When FALSE, counter running total charges are not prorated and are billed for
                the entire billing period.

              _(Optional)_.

          running_total_bill_in_advance: The default value is **TRUE**.

              - When TRUE, running totals are billed at the start of each billing period.

              - When FALSE, running totals are billed at the end of each billing period.

              _(Optional)_.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            body=maybe_transform(
                {
                    "counter_id": counter_id,
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "pro_rate_adjustment_credit": pro_rate_adjustment_credit,
                    "pro_rate_adjustment_debit": pro_rate_adjustment_debit,
                    "pro_rate_running_total": pro_rate_running_total,
                    "running_total_bill_in_advance": running_total_bill_in_advance,
                    "version": version,
                },
                counter_pricing_update_params.CounterPricingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[CounterPricingResponse]:
        """
        Retrieve a list of CounterPricing entities filtered by date, Plan ID, Plan
        Template ID, or CounterPricing ID.

        Args:
          date: Date on which to retrieve active CounterPricings.

          ids: List of CounterPricing IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of CounterPricings to retrieve per page.

          plan_id: UUID of the Plan to retrieve CounterPricings for.

          plan_template_id: UUID of the Plan Template to retrieve CounterPricings for.

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
            f"/organizations/{org_id}/counterpricings",
            page=SyncCursor[CounterPricingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date": date,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan_id": plan_id,
                        "plan_template_id": plan_template_id,
                    },
                    counter_pricing_list_params.CounterPricingListParams,
                ),
            ),
            model=CounterPricingResponse,
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
    ) -> CounterPricingResponse:
        """
        Delete a CounterPricing for the given UUID.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )


class AsyncCounterPricingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCounterPricingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCounterPricingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCounterPricingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCounterPricingsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        counter_id: str,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        pro_rate_adjustment_credit: bool | Omit = omit,
        pro_rate_adjustment_debit: bool | Omit = omit,
        pro_rate_running_total: bool | Omit = omit,
        running_total_bill_in_advance: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterPricingResponse:
        """
        Create a new CounterPricing.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          counter_id: UUID of the Counter used to create the pricing.

          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          code: Unique short code for the Pricing.

          cumulative: Controls whether or not charge rates under a set of pricing bands configured for
              a Pricing are applied according to each separate band or at the highest band
              reached.

              _(Optional)_. The default value is **FALSE**.

              - When TRUE, at billing charge rates are applied according to each separate
                band.

              - When FALSE, at billing charge rates are applied according to highest band
                reached.

              **NOTE:** Use the `cumulative` parameter to create the type of Pricing you
              require. For example, for Tiered Pricing set to **TRUE**; for Volume Pricing,
              set to **FALSE**.

          description: Displayed on Bill line items.

          end_date: The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
              the Plan or Plan Template.

              _(Optional)_ If not specified, the Pricing remains active indefinitely.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          pro_rate_adjustment_credit: The default value is **TRUE**.

              - When TRUE, counter adjustment credits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment credits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_adjustment_debit: The default value is **TRUE**.

              - When TRUE, counter adjustment debits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment debits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_running_total: The default value is **TRUE**.

              - When TRUE, counter running total charges are prorated and are billed according
                to the number of days in billing period.

              - When FALSE, counter running total charges are not prorated and are billed for
                the entire billing period.

              _(Optional)_.

          running_total_bill_in_advance: The default value is **TRUE**.

              - When TRUE, running totals are billed at the start of each billing period.

              - When FALSE, running totals are billed at the end of each billing period.

              _(Optional)_.

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
            f"/organizations/{org_id}/counterpricings",
            body=await async_maybe_transform(
                {
                    "counter_id": counter_id,
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "pro_rate_adjustment_credit": pro_rate_adjustment_credit,
                    "pro_rate_adjustment_debit": pro_rate_adjustment_debit,
                    "pro_rate_running_total": pro_rate_running_total,
                    "running_total_bill_in_advance": running_total_bill_in_advance,
                    "version": version,
                },
                counter_pricing_create_params.CounterPricingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
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
    ) -> CounterPricingResponse:
        """
        Retrieve a CounterPricing for the given UUID.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        counter_id: str,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        pro_rate_adjustment_credit: bool | Omit = omit,
        pro_rate_adjustment_debit: bool | Omit = omit,
        pro_rate_running_total: bool | Omit = omit,
        running_total_bill_in_advance: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CounterPricingResponse:
        """
        Update CounterPricing for the given UUID.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          counter_id: UUID of the Counter used to create the pricing.

          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          code: Unique short code for the Pricing.

          cumulative: Controls whether or not charge rates under a set of pricing bands configured for
              a Pricing are applied according to each separate band or at the highest band
              reached.

              _(Optional)_. The default value is **FALSE**.

              - When TRUE, at billing charge rates are applied according to each separate
                band.

              - When FALSE, at billing charge rates are applied according to highest band
                reached.

              **NOTE:** Use the `cumulative` parameter to create the type of Pricing you
              require. For example, for Tiered Pricing set to **TRUE**; for Volume Pricing,
              set to **FALSE**.

          description: Displayed on Bill line items.

          end_date: The end date _(in ISO-8601 format)_ for when the Pricing ceases to be active for
              the Plan or Plan Template.

              _(Optional)_ If not specified, the Pricing remains active indefinitely.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          pro_rate_adjustment_credit: The default value is **TRUE**.

              - When TRUE, counter adjustment credits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment credits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_adjustment_debit: The default value is **TRUE**.

              - When TRUE, counter adjustment debits are prorated and are billed according to
                the number of days in billing period.

              - When FALSE, counter adjustment debits are not prorated and are billed for the
                entire billing period.

              _(Optional)_.

          pro_rate_running_total: The default value is **TRUE**.

              - When TRUE, counter running total charges are prorated and are billed according
                to the number of days in billing period.

              - When FALSE, counter running total charges are not prorated and are billed for
                the entire billing period.

              _(Optional)_.

          running_total_bill_in_advance: The default value is **TRUE**.

              - When TRUE, running totals are billed at the start of each billing period.

              - When FALSE, running totals are billed at the end of each billing period.

              _(Optional)_.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            body=await async_maybe_transform(
                {
                    "counter_id": counter_id,
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "pro_rate_adjustment_credit": pro_rate_adjustment_credit,
                    "pro_rate_adjustment_debit": pro_rate_adjustment_debit,
                    "pro_rate_running_total": pro_rate_running_total,
                    "running_total_bill_in_advance": running_total_bill_in_advance,
                    "version": version,
                },
                counter_pricing_update_params.CounterPricingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        date: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[CounterPricingResponse, AsyncCursor[CounterPricingResponse]]:
        """
        Retrieve a list of CounterPricing entities filtered by date, Plan ID, Plan
        Template ID, or CounterPricing ID.

        Args:
          date: Date on which to retrieve active CounterPricings.

          ids: List of CounterPricing IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of CounterPricings to retrieve per page.

          plan_id: UUID of the Plan to retrieve CounterPricings for.

          plan_template_id: UUID of the Plan Template to retrieve CounterPricings for.

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
            f"/organizations/{org_id}/counterpricings",
            page=AsyncCursor[CounterPricingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "date": date,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan_id": plan_id,
                        "plan_template_id": plan_template_id,
                    },
                    counter_pricing_list_params.CounterPricingListParams,
                ),
            ),
            model=CounterPricingResponse,
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
    ) -> CounterPricingResponse:
        """
        Delete a CounterPricing for the given UUID.

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
            f"/organizations/{org_id}/counterpricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CounterPricingResponse,
        )


class CounterPricingsResourceWithRawResponse:
    def __init__(self, counter_pricings: CounterPricingsResource) -> None:
        self._counter_pricings = counter_pricings

        self.create = to_raw_response_wrapper(
            counter_pricings.create,
        )
        self.retrieve = to_raw_response_wrapper(
            counter_pricings.retrieve,
        )
        self.update = to_raw_response_wrapper(
            counter_pricings.update,
        )
        self.list = to_raw_response_wrapper(
            counter_pricings.list,
        )
        self.delete = to_raw_response_wrapper(
            counter_pricings.delete,
        )


class AsyncCounterPricingsResourceWithRawResponse:
    def __init__(self, counter_pricings: AsyncCounterPricingsResource) -> None:
        self._counter_pricings = counter_pricings

        self.create = async_to_raw_response_wrapper(
            counter_pricings.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            counter_pricings.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            counter_pricings.update,
        )
        self.list = async_to_raw_response_wrapper(
            counter_pricings.list,
        )
        self.delete = async_to_raw_response_wrapper(
            counter_pricings.delete,
        )


class CounterPricingsResourceWithStreamingResponse:
    def __init__(self, counter_pricings: CounterPricingsResource) -> None:
        self._counter_pricings = counter_pricings

        self.create = to_streamed_response_wrapper(
            counter_pricings.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            counter_pricings.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            counter_pricings.update,
        )
        self.list = to_streamed_response_wrapper(
            counter_pricings.list,
        )
        self.delete = to_streamed_response_wrapper(
            counter_pricings.delete,
        )


class AsyncCounterPricingsResourceWithStreamingResponse:
    def __init__(self, counter_pricings: AsyncCounterPricingsResource) -> None:
        self._counter_pricings = counter_pricings

        self.create = async_to_streamed_response_wrapper(
            counter_pricings.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            counter_pricings.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            counter_pricings.update,
        )
        self.list = async_to_streamed_response_wrapper(
            counter_pricings.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            counter_pricings.delete,
        )
