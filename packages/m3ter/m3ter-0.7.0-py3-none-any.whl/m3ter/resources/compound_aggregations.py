# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal

import httpx

from ..types import (
    compound_aggregation_list_params,
    compound_aggregation_create_params,
    compound_aggregation_update_params,
)
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
from ..types.aggregation_response import AggregationResponse
from ..types.compound_aggregation_response import CompoundAggregationResponse

__all__ = ["CompoundAggregationsResource", "AsyncCompoundAggregationsResource"]


class CompoundAggregationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CompoundAggregationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CompoundAggregationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CompoundAggregationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CompoundAggregationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        calculation: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        evaluate_null_aggregations: bool | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Create a new CompoundAggregation.

        This endpoint allows you to create a new CompoundAggregation for a specific
        Organization. The request body must include all the necessary details such as
        the Calculation formula.

        Args:
          calculation: String that represents the formula for the calculation. This formula determines
              how the CompoundAggregation value is calculated. The calculation can reference
              simple Aggregations or Custom Fields. This field is required when creating or
              updating a CompoundAggregation.

              **NOTE:** If a simple Aggregation referenced by a Compound Aggregation has a
              **Quantity per unit** defined or a **Rounding** defined, these will not be
              factored into the value used by the calculation. For example, if the simple
              Aggregation referenced has a base value of 100 and has **Quantity per unit** set
              at 10, the Compound Aggregation calculation _will use the base value of 100 not
              10_.

          name: Descriptive name for the Aggregation.

          quantity_per_unit: Defines how much of a quantity equates to 1 unit. Used when setting the price
              per unit for billing purposes - if charging for kilobytes per second (KiBy/s) at
              rate of $0.25 per 500 KiBy/s, then set quantityPerUnit to 500 and price Plan at
              $0.25 per unit.

              **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
              typically set to `"UP"`.

          rounding: Specifies how you want to deal with non-integer, fractional number Aggregation
              values.

              **NOTES:**

              - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
                rounded to 4.
              - Also used in combination with `quantityPerUnit`. Rounds the number of units
                after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
                other than one, you would typically set Rounding to **UP**. For example,
                suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
                500, and set charge rate at $0.25 per unit used. If your customer used 48,900
                KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
                to 98 \\** 0.25 = $2.45.

              Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          evaluate_null_aggregations:
              Boolean True / False flag:

              - **TRUE** - set to TRUE if you want to allow null values from the simple
                Aggregations referenced in the Compound Aggregation to be passed in. Simple
                Aggregations based on Meter Target Fields where no usage data is available
                will have null values.
              - **FALSE** Default.

              **Note:** If any of the simple Aggregations you reference in a Compound
              Aggregation calculation might have null values, you must set their Default Value
              to 0. This ensures that any null values passed into the Compound Aggregation are
              passed in correctly with value = 0.

          product_id: Unique identifier (UUID) of the Product the CompoundAggregation belongs to.

              **Note:** Omit this parameter if you want to create a _Global_
              CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations",
            body=maybe_transform(
                {
                    "calculation": calculation,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "evaluate_null_aggregations": evaluate_null_aggregations,
                    "product_id": product_id,
                    "version": version,
                },
                compound_aggregation_create_params.CompoundAggregationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
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
    ) -> CompoundAggregationResponse:
        """
        Retrieve a CompoundAggregation using the given UUID.

        This endpoint returns a specific CompoundAggregation associated with an
        Organization. It provides detailed information about the CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompoundAggregationResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        calculation: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        evaluate_null_aggregations: bool | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Update the CompoundAggregation with the given UUID.

        This endpoint allows you to update the details of a specific CompoundAggregation
        associated with an Organization. Use it to modify details of an existing
        CompoundAggregation such as the Calculation formula.

        **Note:** If you have created Custom Fields for a Compound Aggregation, when you
        use this endpoint to update the Compound Aggregation use the `customFields`
        parameter to preserve those Custom Fields. If you omit them from the update
        request, they will be lost.

        Args:
          calculation: String that represents the formula for the calculation. This formula determines
              how the CompoundAggregation value is calculated. The calculation can reference
              simple Aggregations or Custom Fields. This field is required when creating or
              updating a CompoundAggregation.

              **NOTE:** If a simple Aggregation referenced by a Compound Aggregation has a
              **Quantity per unit** defined or a **Rounding** defined, these will not be
              factored into the value used by the calculation. For example, if the simple
              Aggregation referenced has a base value of 100 and has **Quantity per unit** set
              at 10, the Compound Aggregation calculation _will use the base value of 100 not
              10_.

          name: Descriptive name for the Aggregation.

          quantity_per_unit: Defines how much of a quantity equates to 1 unit. Used when setting the price
              per unit for billing purposes - if charging for kilobytes per second (KiBy/s) at
              rate of $0.25 per 500 KiBy/s, then set quantityPerUnit to 500 and price Plan at
              $0.25 per unit.

              **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
              typically set to `"UP"`.

          rounding: Specifies how you want to deal with non-integer, fractional number Aggregation
              values.

              **NOTES:**

              - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
                rounded to 4.
              - Also used in combination with `quantityPerUnit`. Rounds the number of units
                after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
                other than one, you would typically set Rounding to **UP**. For example,
                suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
                500, and set charge rate at $0.25 per unit used. If your customer used 48,900
                KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
                to 98 \\** 0.25 = $2.45.

              Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          evaluate_null_aggregations:
              Boolean True / False flag:

              - **TRUE** - set to TRUE if you want to allow null values from the simple
                Aggregations referenced in the Compound Aggregation to be passed in. Simple
                Aggregations based on Meter Target Fields where no usage data is available
                will have null values.
              - **FALSE** Default.

              **Note:** If any of the simple Aggregations you reference in a Compound
              Aggregation calculation might have null values, you must set their Default Value
              to 0. This ensures that any null values passed into the Compound Aggregation are
              passed in correctly with value = 0.

          product_id: Unique identifier (UUID) of the Product the CompoundAggregation belongs to.

              **Note:** Omit this parameter if you want to create a _Global_
              CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            body=maybe_transform(
                {
                    "calculation": calculation,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "evaluate_null_aggregations": evaluate_null_aggregations,
                    "product_id": product_id,
                    "version": version,
                },
                compound_aggregation_update_params.CompoundAggregationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
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
    ) -> SyncCursor[CompoundAggregationResponse]:
        """
        Retrieve a list of all CompoundAggregations.

        This endpoint retrieves a list of CompoundAggregations associated with a
        specific organization. CompoundAggregations enable you to define numerical
        measures based on simple Aggregations of usage data. It supports pagination, and
        includes various query parameters to filter the CompoundAggregations based on
        Product, CompoundAggregation IDs or short codes.

        Args:
          codes: An optional parameter to retrieve specific CompoundAggregations based on their
              short codes.

          ids: An optional parameter to retrieve specific CompoundAggregations based on their
              unique identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              CompoundAggregations in a paginated list.

          page_size: Specifies the maximum number of CompoundAggregations to retrieve per page.

          product_id: An optional parameter to filter the CompoundAggregations based on specific
              Product unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/compoundaggregations",
            page=SyncCursor[CompoundAggregationResponse],
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
                    compound_aggregation_list_params.CompoundAggregationListParams,
                ),
            ),
            model=CompoundAggregationResponse,
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
    ) -> CompoundAggregationResponse:
        """
        Delete a CompoundAggregation with the given UUID.

        This endpoint enables deletion of a specific CompoundAggregation associated with
        a specific Organization. Useful when you need to remove an existing
        CompoundAggregation that is no longer required, such as when changing pricing or
        planning models.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompoundAggregationResponse,
        )


class AsyncCompoundAggregationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCompoundAggregationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCompoundAggregationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCompoundAggregationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCompoundAggregationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        calculation: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        evaluate_null_aggregations: bool | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Create a new CompoundAggregation.

        This endpoint allows you to create a new CompoundAggregation for a specific
        Organization. The request body must include all the necessary details such as
        the Calculation formula.

        Args:
          calculation: String that represents the formula for the calculation. This formula determines
              how the CompoundAggregation value is calculated. The calculation can reference
              simple Aggregations or Custom Fields. This field is required when creating or
              updating a CompoundAggregation.

              **NOTE:** If a simple Aggregation referenced by a Compound Aggregation has a
              **Quantity per unit** defined or a **Rounding** defined, these will not be
              factored into the value used by the calculation. For example, if the simple
              Aggregation referenced has a base value of 100 and has **Quantity per unit** set
              at 10, the Compound Aggregation calculation _will use the base value of 100 not
              10_.

          name: Descriptive name for the Aggregation.

          quantity_per_unit: Defines how much of a quantity equates to 1 unit. Used when setting the price
              per unit for billing purposes - if charging for kilobytes per second (KiBy/s) at
              rate of $0.25 per 500 KiBy/s, then set quantityPerUnit to 500 and price Plan at
              $0.25 per unit.

              **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
              typically set to `"UP"`.

          rounding: Specifies how you want to deal with non-integer, fractional number Aggregation
              values.

              **NOTES:**

              - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
                rounded to 4.
              - Also used in combination with `quantityPerUnit`. Rounds the number of units
                after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
                other than one, you would typically set Rounding to **UP**. For example,
                suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
                500, and set charge rate at $0.25 per unit used. If your customer used 48,900
                KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
                to 98 \\** 0.25 = $2.45.

              Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          evaluate_null_aggregations:
              Boolean True / False flag:

              - **TRUE** - set to TRUE if you want to allow null values from the simple
                Aggregations referenced in the Compound Aggregation to be passed in. Simple
                Aggregations based on Meter Target Fields where no usage data is available
                will have null values.
              - **FALSE** Default.

              **Note:** If any of the simple Aggregations you reference in a Compound
              Aggregation calculation might have null values, you must set their Default Value
              to 0. This ensures that any null values passed into the Compound Aggregation are
              passed in correctly with value = 0.

          product_id: Unique identifier (UUID) of the Product the CompoundAggregation belongs to.

              **Note:** Omit this parameter if you want to create a _Global_
              CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations",
            body=await async_maybe_transform(
                {
                    "calculation": calculation,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "evaluate_null_aggregations": evaluate_null_aggregations,
                    "product_id": product_id,
                    "version": version,
                },
                compound_aggregation_create_params.CompoundAggregationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
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
    ) -> CompoundAggregationResponse:
        """
        Retrieve a CompoundAggregation using the given UUID.

        This endpoint returns a specific CompoundAggregation associated with an
        Organization. It provides detailed information about the CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompoundAggregationResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        calculation: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        evaluate_null_aggregations: bool | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Update the CompoundAggregation with the given UUID.

        This endpoint allows you to update the details of a specific CompoundAggregation
        associated with an Organization. Use it to modify details of an existing
        CompoundAggregation such as the Calculation formula.

        **Note:** If you have created Custom Fields for a Compound Aggregation, when you
        use this endpoint to update the Compound Aggregation use the `customFields`
        parameter to preserve those Custom Fields. If you omit them from the update
        request, they will be lost.

        Args:
          calculation: String that represents the formula for the calculation. This formula determines
              how the CompoundAggregation value is calculated. The calculation can reference
              simple Aggregations or Custom Fields. This field is required when creating or
              updating a CompoundAggregation.

              **NOTE:** If a simple Aggregation referenced by a Compound Aggregation has a
              **Quantity per unit** defined or a **Rounding** defined, these will not be
              factored into the value used by the calculation. For example, if the simple
              Aggregation referenced has a base value of 100 and has **Quantity per unit** set
              at 10, the Compound Aggregation calculation _will use the base value of 100 not
              10_.

          name: Descriptive name for the Aggregation.

          quantity_per_unit: Defines how much of a quantity equates to 1 unit. Used when setting the price
              per unit for billing purposes - if charging for kilobytes per second (KiBy/s) at
              rate of $0.25 per 500 KiBy/s, then set quantityPerUnit to 500 and price Plan at
              $0.25 per unit.

              **Note:** If `quantityPerUnit` is set to a value other than one, `rounding` is
              typically set to `"UP"`.

          rounding: Specifies how you want to deal with non-integer, fractional number Aggregation
              values.

              **NOTES:**

              - **NEAREST** rounds to the nearest half: 5.1 is rounded to 5, and 3.5 is
                rounded to 4.
              - Also used in combination with `quantityPerUnit`. Rounds the number of units
                after `quantityPerUnit` is applied. If you set `quantityPerUnit` to a value
                other than one, you would typically set Rounding to **UP**. For example,
                suppose you charge by kilobytes per second (KiBy/s), set `quantityPerUnit` =
                500, and set charge rate at $0.25 per unit used. If your customer used 48,900
                KiBy/s in a billing period, the charge would be 48,900 / 500 = 97.8 rounded up
                to 98 \\** 0.25 = $2.45.

              Enum: ???UP??? ???DOWN??? ???NEAREST??? ???NONE???

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          evaluate_null_aggregations:
              Boolean True / False flag:

              - **TRUE** - set to TRUE if you want to allow null values from the simple
                Aggregations referenced in the Compound Aggregation to be passed in. Simple
                Aggregations based on Meter Target Fields where no usage data is available
                will have null values.
              - **FALSE** Default.

              **Note:** If any of the simple Aggregations you reference in a Compound
              Aggregation calculation might have null values, you must set their Default Value
              to 0. This ensures that any null values passed into the Compound Aggregation are
              passed in correctly with value = 0.

          product_id: Unique identifier (UUID) of the Product the CompoundAggregation belongs to.

              **Note:** Omit this parameter if you want to create a _Global_
              CompoundAggregation.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            body=await async_maybe_transform(
                {
                    "calculation": calculation,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "evaluate_null_aggregations": evaluate_null_aggregations,
                    "product_id": product_id,
                    "version": version,
                },
                compound_aggregation_update_params.CompoundAggregationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
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
    ) -> AsyncPaginator[CompoundAggregationResponse, AsyncCursor[CompoundAggregationResponse]]:
        """
        Retrieve a list of all CompoundAggregations.

        This endpoint retrieves a list of CompoundAggregations associated with a
        specific organization. CompoundAggregations enable you to define numerical
        measures based on simple Aggregations of usage data. It supports pagination, and
        includes various query parameters to filter the CompoundAggregations based on
        Product, CompoundAggregation IDs or short codes.

        Args:
          codes: An optional parameter to retrieve specific CompoundAggregations based on their
              short codes.

          ids: An optional parameter to retrieve specific CompoundAggregations based on their
              unique identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              CompoundAggregations in a paginated list.

          page_size: Specifies the maximum number of CompoundAggregations to retrieve per page.

          product_id: An optional parameter to filter the CompoundAggregations based on specific
              Product unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/compoundaggregations",
            page=AsyncCursor[CompoundAggregationResponse],
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
                    compound_aggregation_list_params.CompoundAggregationListParams,
                ),
            ),
            model=CompoundAggregationResponse,
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
    ) -> CompoundAggregationResponse:
        """
        Delete a CompoundAggregation with the given UUID.

        This endpoint enables deletion of a specific CompoundAggregation associated with
        a specific Organization. Useful when you need to remove an existing
        CompoundAggregation that is no longer required, such as when changing pricing or
        planning models.

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
            f"/organizations/{org_id}/compoundaggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompoundAggregationResponse,
        )


class CompoundAggregationsResourceWithRawResponse:
    def __init__(self, compound_aggregations: CompoundAggregationsResource) -> None:
        self._compound_aggregations = compound_aggregations

        self.create = to_raw_response_wrapper(
            compound_aggregations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            compound_aggregations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            compound_aggregations.update,
        )
        self.list = to_raw_response_wrapper(
            compound_aggregations.list,
        )
        self.delete = to_raw_response_wrapper(
            compound_aggregations.delete,
        )


class AsyncCompoundAggregationsResourceWithRawResponse:
    def __init__(self, compound_aggregations: AsyncCompoundAggregationsResource) -> None:
        self._compound_aggregations = compound_aggregations

        self.create = async_to_raw_response_wrapper(
            compound_aggregations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            compound_aggregations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            compound_aggregations.update,
        )
        self.list = async_to_raw_response_wrapper(
            compound_aggregations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            compound_aggregations.delete,
        )


class CompoundAggregationsResourceWithStreamingResponse:
    def __init__(self, compound_aggregations: CompoundAggregationsResource) -> None:
        self._compound_aggregations = compound_aggregations

        self.create = to_streamed_response_wrapper(
            compound_aggregations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            compound_aggregations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            compound_aggregations.update,
        )
        self.list = to_streamed_response_wrapper(
            compound_aggregations.list,
        )
        self.delete = to_streamed_response_wrapper(
            compound_aggregations.delete,
        )


class AsyncCompoundAggregationsResourceWithStreamingResponse:
    def __init__(self, compound_aggregations: AsyncCompoundAggregationsResource) -> None:
        self._compound_aggregations = compound_aggregations

        self.create = async_to_streamed_response_wrapper(
            compound_aggregations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            compound_aggregations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            compound_aggregations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            compound_aggregations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            compound_aggregations.delete,
        )
