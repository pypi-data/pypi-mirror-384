# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from typing_extensions import Literal

import httpx

from ..types import aggregation_list_params, aggregation_create_params, aggregation_update_params
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

__all__ = ["AggregationsResource", "AsyncAggregationsResource"]


class AggregationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AggregationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AggregationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AggregationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AggregationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        aggregation: Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"],
        meter_id: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        target_field: str,
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        custom_sql: str | Omit = omit,
        default_value: float | Omit = omit,
        segmented_fields: SequenceNotStr[str] | Omit = omit,
        segments: Iterable[Dict[str, str]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Create a new Aggregation.

        Args:
          aggregation: Specifies the computation method applied to usage data collected in
              `targetField`. Aggregation unit value depends on the **Category** configured for
              the selected targetField.

              Enum:

              - **SUM**. Adds the values. Can be applied to a **Measure**, **Income**, or
                **Cost** `targetField`.

              - **MIN**. Uses the minimum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **MAX**. Uses the maximum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **COUNT**. Counts the number of values. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`.

              - **LATEST**. Uses the most recent value. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`. Note: Based on the timestamp (`ts`)
                value of usage data measurement submissions. If using this method, please
                ensure _distinct_ `ts` values are used for usage data measurment submissions.

              - **MEAN**. Uses the arithmetic mean of the values. Can be applied to a
                **Measure**, **Income**, or **Cost** `targetField`.

              - **UNIQUE**. Uses unique values and returns a count of the number of unique
                values. Can be applied to a **Metadata** `targetField`.

          meter_id: The UUID of the Meter used as the source of usage data for the Aggregation.

              Each Aggregation is a child of a Meter, so the Meter must be selected.

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

          target_field: `Code` of the target `dataField` or `derivedField` on the Meter used as the
              basis for the Aggregation.

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          custom_sql: **NOTE:** The `customSql` Aggregation type is currently only available in Beta
              release and on request. If you are interested in using this feature, please get
              in touch with m3ter Support or your m3ter contact.

          default_value: Aggregation value used when no usage data is available to be aggregated.
              _(Optional)_.

              **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
              Aggregation. This ensures that any null values are passed in correctly to the
              Compound Aggregation calculation with a value = 0.

          segmented_fields: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segments`.

              Enter the `Codes` of the fields in the target Meter to use for segmentation
              purposes.

              String `dataFields` on the target Meter can be segmented. Any string
              `derivedFields` on the target Meter, such as one that concatenates two string
              `dataFields`, can also be segmented.

          segments: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segmentedFields`.

              Enter the values that are to be used as the segments, read from the fields in
              the meter pointed at by `segmentedFields`.

              Note that you can use _wildcards_ or _defaults_ when setting up segment values.
              For more details on how to do this with an example, see
              [Using Wildcards - API Calls](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/segmented-aggregations#using-wildcards---api-calls)
              in our main User Docs.

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
            f"/organizations/{org_id}/aggregations",
            body=maybe_transform(
                {
                    "aggregation": aggregation,
                    "meter_id": meter_id,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "target_field": target_field,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "custom_sql": custom_sql,
                    "default_value": default_value,
                    "segmented_fields": segmented_fields,
                    "segments": segments,
                    "version": version,
                },
                aggregation_create_params.AggregationCreateParams,
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
    ) -> AggregationResponse:
        """
        Retrieve the Aggregation with the given UUID.

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
            f"/organizations/{org_id}/aggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        aggregation: Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"],
        meter_id: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        target_field: str,
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        custom_sql: str | Omit = omit,
        default_value: float | Omit = omit,
        segmented_fields: SequenceNotStr[str] | Omit = omit,
        segments: Iterable[Dict[str, str]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Update the Aggregation with the given UUID.

        **Note:** If you have created Custom Fields for an Aggregation, when you use
        this endpoint to update the Aggregation use the `customFields` parameter to
        preserve those Custom Fields. If you omit them from the update request, they
        will be lost.

        Args:
          aggregation: Specifies the computation method applied to usage data collected in
              `targetField`. Aggregation unit value depends on the **Category** configured for
              the selected targetField.

              Enum:

              - **SUM**. Adds the values. Can be applied to a **Measure**, **Income**, or
                **Cost** `targetField`.

              - **MIN**. Uses the minimum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **MAX**. Uses the maximum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **COUNT**. Counts the number of values. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`.

              - **LATEST**. Uses the most recent value. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`. Note: Based on the timestamp (`ts`)
                value of usage data measurement submissions. If using this method, please
                ensure _distinct_ `ts` values are used for usage data measurment submissions.

              - **MEAN**. Uses the arithmetic mean of the values. Can be applied to a
                **Measure**, **Income**, or **Cost** `targetField`.

              - **UNIQUE**. Uses unique values and returns a count of the number of unique
                values. Can be applied to a **Metadata** `targetField`.

          meter_id: The UUID of the Meter used as the source of usage data for the Aggregation.

              Each Aggregation is a child of a Meter, so the Meter must be selected.

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

          target_field: `Code` of the target `dataField` or `derivedField` on the Meter used as the
              basis for the Aggregation.

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          custom_sql: **NOTE:** The `customSql` Aggregation type is currently only available in Beta
              release and on request. If you are interested in using this feature, please get
              in touch with m3ter Support or your m3ter contact.

          default_value: Aggregation value used when no usage data is available to be aggregated.
              _(Optional)_.

              **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
              Aggregation. This ensures that any null values are passed in correctly to the
              Compound Aggregation calculation with a value = 0.

          segmented_fields: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segments`.

              Enter the `Codes` of the fields in the target Meter to use for segmentation
              purposes.

              String `dataFields` on the target Meter can be segmented. Any string
              `derivedFields` on the target Meter, such as one that concatenates two string
              `dataFields`, can also be segmented.

          segments: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segmentedFields`.

              Enter the values that are to be used as the segments, read from the fields in
              the meter pointed at by `segmentedFields`.

              Note that you can use _wildcards_ or _defaults_ when setting up segment values.
              For more details on how to do this with an example, see
              [Using Wildcards - API Calls](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/segmented-aggregations#using-wildcards---api-calls)
              in our main User Docs.

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
            f"/organizations/{org_id}/aggregations/{id}",
            body=maybe_transform(
                {
                    "aggregation": aggregation,
                    "meter_id": meter_id,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "target_field": target_field,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "custom_sql": custom_sql,
                    "default_value": default_value,
                    "segmented_fields": segmented_fields,
                    "segments": segments,
                    "version": version,
                },
                aggregation_update_params.AggregationUpdateParams,
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
    ) -> SyncCursor[AggregationResponse]:
        """
        Retrieve a list of Aggregations that can be filtered by Product, Aggregation ID,
        or Code.

        Args:
          codes: List of Aggregation codes to retrieve. These are unique short codes to identify
              each Aggregation.

          ids: List of Aggregation IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Aggregations to retrieve per page.

          product_id: The UUIDs of the Products to retrieve Aggregations for.

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
            f"/organizations/{org_id}/aggregations",
            page=SyncCursor[AggregationResponse],
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
                    aggregation_list_params.AggregationListParams,
                ),
            ),
            model=AggregationResponse,
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
    ) -> AggregationResponse:
        """
        Delete the Aggregation with the given UUID.

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
            f"/organizations/{org_id}/aggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
        )


class AsyncAggregationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAggregationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAggregationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAggregationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncAggregationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        aggregation: Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"],
        meter_id: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        target_field: str,
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        custom_sql: str | Omit = omit,
        default_value: float | Omit = omit,
        segmented_fields: SequenceNotStr[str] | Omit = omit,
        segments: Iterable[Dict[str, str]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Create a new Aggregation.

        Args:
          aggregation: Specifies the computation method applied to usage data collected in
              `targetField`. Aggregation unit value depends on the **Category** configured for
              the selected targetField.

              Enum:

              - **SUM**. Adds the values. Can be applied to a **Measure**, **Income**, or
                **Cost** `targetField`.

              - **MIN**. Uses the minimum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **MAX**. Uses the maximum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **COUNT**. Counts the number of values. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`.

              - **LATEST**. Uses the most recent value. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`. Note: Based on the timestamp (`ts`)
                value of usage data measurement submissions. If using this method, please
                ensure _distinct_ `ts` values are used for usage data measurment submissions.

              - **MEAN**. Uses the arithmetic mean of the values. Can be applied to a
                **Measure**, **Income**, or **Cost** `targetField`.

              - **UNIQUE**. Uses unique values and returns a count of the number of unique
                values. Can be applied to a **Metadata** `targetField`.

          meter_id: The UUID of the Meter used as the source of usage data for the Aggregation.

              Each Aggregation is a child of a Meter, so the Meter must be selected.

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

          target_field: `Code` of the target `dataField` or `derivedField` on the Meter used as the
              basis for the Aggregation.

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          custom_sql: **NOTE:** The `customSql` Aggregation type is currently only available in Beta
              release and on request. If you are interested in using this feature, please get
              in touch with m3ter Support or your m3ter contact.

          default_value: Aggregation value used when no usage data is available to be aggregated.
              _(Optional)_.

              **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
              Aggregation. This ensures that any null values are passed in correctly to the
              Compound Aggregation calculation with a value = 0.

          segmented_fields: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segments`.

              Enter the `Codes` of the fields in the target Meter to use for segmentation
              purposes.

              String `dataFields` on the target Meter can be segmented. Any string
              `derivedFields` on the target Meter, such as one that concatenates two string
              `dataFields`, can also be segmented.

          segments: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segmentedFields`.

              Enter the values that are to be used as the segments, read from the fields in
              the meter pointed at by `segmentedFields`.

              Note that you can use _wildcards_ or _defaults_ when setting up segment values.
              For more details on how to do this with an example, see
              [Using Wildcards - API Calls](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/segmented-aggregations#using-wildcards---api-calls)
              in our main User Docs.

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
            f"/organizations/{org_id}/aggregations",
            body=await async_maybe_transform(
                {
                    "aggregation": aggregation,
                    "meter_id": meter_id,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "target_field": target_field,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "custom_sql": custom_sql,
                    "default_value": default_value,
                    "segmented_fields": segmented_fields,
                    "segments": segments,
                    "version": version,
                },
                aggregation_create_params.AggregationCreateParams,
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
    ) -> AggregationResponse:
        """
        Retrieve the Aggregation with the given UUID.

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
            f"/organizations/{org_id}/aggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        aggregation: Literal["SUM", "MIN", "MAX", "COUNT", "LATEST", "MEAN", "UNIQUE", "CUSTOM_SQL"],
        meter_id: str,
        name: str,
        quantity_per_unit: float,
        rounding: Literal["UP", "DOWN", "NEAREST", "NONE"],
        target_field: str,
        unit: str,
        accounting_product_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        custom_sql: str | Omit = omit,
        default_value: float | Omit = omit,
        segmented_fields: SequenceNotStr[str] | Omit = omit,
        segments: Iterable[Dict[str, str]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AggregationResponse:
        """
        Update the Aggregation with the given UUID.

        **Note:** If you have created Custom Fields for an Aggregation, when you use
        this endpoint to update the Aggregation use the `customFields` parameter to
        preserve those Custom Fields. If you omit them from the update request, they
        will be lost.

        Args:
          aggregation: Specifies the computation method applied to usage data collected in
              `targetField`. Aggregation unit value depends on the **Category** configured for
              the selected targetField.

              Enum:

              - **SUM**. Adds the values. Can be applied to a **Measure**, **Income**, or
                **Cost** `targetField`.

              - **MIN**. Uses the minimum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **MAX**. Uses the maximum value. Can be applied to a **Measure**, **Income**,
                or **Cost** `targetField`.

              - **COUNT**. Counts the number of values. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`.

              - **LATEST**. Uses the most recent value. Can be applied to a **Measure**,
                **Income**, or **Cost** `targetField`. Note: Based on the timestamp (`ts`)
                value of usage data measurement submissions. If using this method, please
                ensure _distinct_ `ts` values are used for usage data measurment submissions.

              - **MEAN**. Uses the arithmetic mean of the values. Can be applied to a
                **Measure**, **Income**, or **Cost** `targetField`.

              - **UNIQUE**. Uses unique values and returns a count of the number of unique
                values. Can be applied to a **Metadata** `targetField`.

          meter_id: The UUID of the Meter used as the source of usage data for the Aggregation.

              Each Aggregation is a child of a Meter, so the Meter must be selected.

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

          target_field: `Code` of the target `dataField` or `derivedField` on the Meter used as the
              basis for the Aggregation.

          unit: User defined label for units shown for Bill line items, indicating to your
              customers what they are being charged for.

          accounting_product_id: Optional Product ID this Aggregation should be attributed to for accounting
              purposes

          code: Code of the new Aggregation. A unique short code to identify the Aggregation.

          custom_sql: **NOTE:** The `customSql` Aggregation type is currently only available in Beta
              release and on request. If you are interested in using this feature, please get
              in touch with m3ter Support or your m3ter contact.

          default_value: Aggregation value used when no usage data is available to be aggregated.
              _(Optional)_.

              **Note:** Set to 0, if you expect to reference the Aggregation in a Compound
              Aggregation. This ensures that any null values are passed in correctly to the
              Compound Aggregation calculation with a value = 0.

          segmented_fields: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segments`.

              Enter the `Codes` of the fields in the target Meter to use for segmentation
              purposes.

              String `dataFields` on the target Meter can be segmented. Any string
              `derivedFields` on the target Meter, such as one that concatenates two string
              `dataFields`, can also be segmented.

          segments: _(Optional)_. Used when creating a segmented Aggregation, which segments the
              usage data collected by a single Meter. Works together with `segmentedFields`.

              Enter the values that are to be used as the segments, read from the fields in
              the meter pointed at by `segmentedFields`.

              Note that you can use _wildcards_ or _defaults_ when setting up segment values.
              For more details on how to do this with an example, see
              [Using Wildcards - API Calls](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/segmented-aggregations#using-wildcards---api-calls)
              in our main User Docs.

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
            f"/organizations/{org_id}/aggregations/{id}",
            body=await async_maybe_transform(
                {
                    "aggregation": aggregation,
                    "meter_id": meter_id,
                    "name": name,
                    "quantity_per_unit": quantity_per_unit,
                    "rounding": rounding,
                    "target_field": target_field,
                    "unit": unit,
                    "accounting_product_id": accounting_product_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "custom_sql": custom_sql,
                    "default_value": default_value,
                    "segmented_fields": segmented_fields,
                    "segments": segments,
                    "version": version,
                },
                aggregation_update_params.AggregationUpdateParams,
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
    ) -> AsyncPaginator[AggregationResponse, AsyncCursor[AggregationResponse]]:
        """
        Retrieve a list of Aggregations that can be filtered by Product, Aggregation ID,
        or Code.

        Args:
          codes: List of Aggregation codes to retrieve. These are unique short codes to identify
              each Aggregation.

          ids: List of Aggregation IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Aggregations to retrieve per page.

          product_id: The UUIDs of the Products to retrieve Aggregations for.

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
            f"/organizations/{org_id}/aggregations",
            page=AsyncCursor[AggregationResponse],
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
                    aggregation_list_params.AggregationListParams,
                ),
            ),
            model=AggregationResponse,
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
    ) -> AggregationResponse:
        """
        Delete the Aggregation with the given UUID.

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
            f"/organizations/{org_id}/aggregations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AggregationResponse,
        )


class AggregationsResourceWithRawResponse:
    def __init__(self, aggregations: AggregationsResource) -> None:
        self._aggregations = aggregations

        self.create = to_raw_response_wrapper(
            aggregations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            aggregations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            aggregations.update,
        )
        self.list = to_raw_response_wrapper(
            aggregations.list,
        )
        self.delete = to_raw_response_wrapper(
            aggregations.delete,
        )


class AsyncAggregationsResourceWithRawResponse:
    def __init__(self, aggregations: AsyncAggregationsResource) -> None:
        self._aggregations = aggregations

        self.create = async_to_raw_response_wrapper(
            aggregations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            aggregations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            aggregations.update,
        )
        self.list = async_to_raw_response_wrapper(
            aggregations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            aggregations.delete,
        )


class AggregationsResourceWithStreamingResponse:
    def __init__(self, aggregations: AggregationsResource) -> None:
        self._aggregations = aggregations

        self.create = to_streamed_response_wrapper(
            aggregations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            aggregations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            aggregations.update,
        )
        self.list = to_streamed_response_wrapper(
            aggregations.list,
        )
        self.delete = to_streamed_response_wrapper(
            aggregations.delete,
        )


class AsyncAggregationsResourceWithStreamingResponse:
    def __init__(self, aggregations: AsyncAggregationsResource) -> None:
        self._aggregations = aggregations

        self.create = async_to_streamed_response_wrapper(
            aggregations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            aggregations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            aggregations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            aggregations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            aggregations.delete,
        )
