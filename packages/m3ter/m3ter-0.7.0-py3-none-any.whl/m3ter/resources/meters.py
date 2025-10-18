# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable

import httpx

from ..types import meter_list_params, meter_create_params, meter_update_params
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
from ..types.meter_response import MeterResponse
from ..types.data_field_param import DataFieldParam
from ..types.derived_field_param import DerivedFieldParam

__all__ = ["MetersResource", "AsyncMetersResource"]


class MetersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MetersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return MetersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MetersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return MetersResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        data_fields: Iterable[DataFieldParam],
        derived_fields: Iterable[DerivedFieldParam],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        group_id: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeterResponse:
        """
        Create a new Meter.

        When you create a Meter, you can define two types of field for usage data
        collection and ingest into the platform:

        - `dataFields` to collect raw usage data measures - numeric quantitative data
          values or non-numeric point data values.
        - `derivedFields` to derive usage data measures that are the result of applying
          a calculation to `dataFields`, `customFields`, or system `Timestamp` fields.

        You can also:

        - Create `customFields` for a Meter, which allows you to attach custom data to
          the Meter as name/value pairs.
        - Create Global Meters, which are not tied to a specific Product and allow you
          collect to usage data that will form the basis of usage-based pricing across
          more than one of your Products.

        **IMPORTANT! - use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any fields you configure for Meters, such
        as Data Fields or Derived Fields, do not contain any end-customer PII data. See
        the [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        See also:

        - [Reviewing Meter Options](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/reviewing-meter-options).

        Args:
          code: Code of the Meter - unique short code used to identify the Meter.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          data_fields: Used to submit categorized raw usage data values for ingest into the platform -
              either numeric quantitative values or non-numeric data values. At least one
              required per Meter; maximum 15 per Meter.

          derived_fields: Used to submit usage data values for ingest into the platform that are the
              result of a calculation performed on `dataFields`, `customFields`, or system
              `Timestamp` fields. Raw usage data is not submitted using `derivedFields`.
              Maximum 15 per Meter. _(Optional)_.

              **Note:** Required parameter. If you want to create a Meter without Derived
              Fields, use an empty array `[]`. If you use a `null`, you'll receive an error.

          name: Descriptive name for the Meter.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          group_id: UUID of the group the Meter belongs to. _(Optional)_.

          product_id: UUID of the product the Meter belongs to. _(Optional)_ - if left blank, the
              Meter is global.

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
            f"/organizations/{org_id}/meters",
            body=maybe_transform(
                {
                    "code": code,
                    "data_fields": data_fields,
                    "derived_fields": derived_fields,
                    "name": name,
                    "custom_fields": custom_fields,
                    "group_id": group_id,
                    "product_id": product_id,
                    "version": version,
                },
                meter_create_params.MeterCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
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
    ) -> MeterResponse:
        """
        Retrieve the Meter with the given UUID.

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
            f"/organizations/{org_id}/meters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        data_fields: Iterable[DataFieldParam],
        derived_fields: Iterable[DerivedFieldParam],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        group_id: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeterResponse:
        """
        Update the Meter with the given UUID.

        **Note:** If you have created Custom Fields for a Meter, when you use this
        endpoint to update the Meter use the `customFields` parameter to preserve those
        Custom Fields. If you omit them from the update request, they will be lost.

        Args:
          code: Code of the Meter - unique short code used to identify the Meter.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          data_fields: Used to submit categorized raw usage data values for ingest into the platform -
              either numeric quantitative values or non-numeric data values. At least one
              required per Meter; maximum 15 per Meter.

          derived_fields: Used to submit usage data values for ingest into the platform that are the
              result of a calculation performed on `dataFields`, `customFields`, or system
              `Timestamp` fields. Raw usage data is not submitted using `derivedFields`.
              Maximum 15 per Meter. _(Optional)_.

              **Note:** Required parameter. If you want to create a Meter without Derived
              Fields, use an empty array `[]`. If you use a `null`, you'll receive an error.

          name: Descriptive name for the Meter.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          group_id: UUID of the group the Meter belongs to. _(Optional)_.

          product_id: UUID of the product the Meter belongs to. _(Optional)_ - if left blank, the
              Meter is global.

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
            f"/organizations/{org_id}/meters/{id}",
            body=maybe_transform(
                {
                    "code": code,
                    "data_fields": data_fields,
                    "derived_fields": derived_fields,
                    "name": name,
                    "custom_fields": custom_fields,
                    "group_id": group_id,
                    "product_id": product_id,
                    "version": version,
                },
                meter_update_params.MeterUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
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
    ) -> SyncCursor[MeterResponse]:
        """
        Retrieve a list of Meters that can be filtered by Product, Meter ID, or Meter
        short code.

        Args:
          codes: List of Meter codes to retrieve. These are the unique short codes that identify
              each Meter.

          ids: List of Meter IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of Meters to retrieve per page.

          product_id: The UUIDs of the Products to retrieve Meters for.

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
            f"/organizations/{org_id}/meters",
            page=SyncCursor[MeterResponse],
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
                    meter_list_params.MeterListParams,
                ),
            ),
            model=MeterResponse,
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
    ) -> MeterResponse:
        """
        Delete the Meter with the given UUID.

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
            f"/organizations/{org_id}/meters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
        )


class AsyncMetersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMetersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncMetersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMetersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncMetersResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        data_fields: Iterable[DataFieldParam],
        derived_fields: Iterable[DerivedFieldParam],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        group_id: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeterResponse:
        """
        Create a new Meter.

        When you create a Meter, you can define two types of field for usage data
        collection and ingest into the platform:

        - `dataFields` to collect raw usage data measures - numeric quantitative data
          values or non-numeric point data values.
        - `derivedFields` to derive usage data measures that are the result of applying
          a calculation to `dataFields`, `customFields`, or system `Timestamp` fields.

        You can also:

        - Create `customFields` for a Meter, which allows you to attach custom data to
          the Meter as name/value pairs.
        - Create Global Meters, which are not tied to a specific Product and allow you
          collect to usage data that will form the basis of usage-based pricing across
          more than one of your Products.

        **IMPORTANT! - use of PII:** The use of any of your end-customers' Personally
        Identifiable Information (PII) in m3ter is restricted to a few fields on the
        **Account** entity. Please ensure that any fields you configure for Meters, such
        as Data Fields or Derived Fields, do not contain any end-customer PII data. See
        the [Introduction section](https://www.m3ter.com/docs/api#section/Introduction)
        above for more details.

        See also:

        - [Reviewing Meter Options](https://www.m3ter.com/docs/guides/setting-up-usage-data-meters-and-aggregations/reviewing-meter-options).

        Args:
          code: Code of the Meter - unique short code used to identify the Meter.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          data_fields: Used to submit categorized raw usage data values for ingest into the platform -
              either numeric quantitative values or non-numeric data values. At least one
              required per Meter; maximum 15 per Meter.

          derived_fields: Used to submit usage data values for ingest into the platform that are the
              result of a calculation performed on `dataFields`, `customFields`, or system
              `Timestamp` fields. Raw usage data is not submitted using `derivedFields`.
              Maximum 15 per Meter. _(Optional)_.

              **Note:** Required parameter. If you want to create a Meter without Derived
              Fields, use an empty array `[]`. If you use a `null`, you'll receive an error.

          name: Descriptive name for the Meter.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          group_id: UUID of the group the Meter belongs to. _(Optional)_.

          product_id: UUID of the product the Meter belongs to. _(Optional)_ - if left blank, the
              Meter is global.

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
            f"/organizations/{org_id}/meters",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "data_fields": data_fields,
                    "derived_fields": derived_fields,
                    "name": name,
                    "custom_fields": custom_fields,
                    "group_id": group_id,
                    "product_id": product_id,
                    "version": version,
                },
                meter_create_params.MeterCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
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
    ) -> MeterResponse:
        """
        Retrieve the Meter with the given UUID.

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
            f"/organizations/{org_id}/meters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        data_fields: Iterable[DataFieldParam],
        derived_fields: Iterable[DerivedFieldParam],
        name: str,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        group_id: str | Omit = omit,
        product_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeterResponse:
        """
        Update the Meter with the given UUID.

        **Note:** If you have created Custom Fields for a Meter, when you use this
        endpoint to update the Meter use the `customFields` parameter to preserve those
        Custom Fields. If you omit them from the update request, they will be lost.

        Args:
          code: Code of the Meter - unique short code used to identify the Meter.

              **NOTE:** Code has a maximum length of 80 characters and must not contain
              non-printable or whitespace characters (except space), and cannot start/end with
              whitespace.

          data_fields: Used to submit categorized raw usage data values for ingest into the platform -
              either numeric quantitative values or non-numeric data values. At least one
              required per Meter; maximum 15 per Meter.

          derived_fields: Used to submit usage data values for ingest into the platform that are the
              result of a calculation performed on `dataFields`, `customFields`, or system
              `Timestamp` fields. Raw usage data is not submitted using `derivedFields`.
              Maximum 15 per Meter. _(Optional)_.

              **Note:** Required parameter. If you want to create a Meter without Derived
              Fields, use an empty array `[]`. If you use a `null`, you'll receive an error.

          name: Descriptive name for the Meter.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          group_id: UUID of the group the Meter belongs to. _(Optional)_.

          product_id: UUID of the product the Meter belongs to. _(Optional)_ - if left blank, the
              Meter is global.

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
            f"/organizations/{org_id}/meters/{id}",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "data_fields": data_fields,
                    "derived_fields": derived_fields,
                    "name": name,
                    "custom_fields": custom_fields,
                    "group_id": group_id,
                    "product_id": product_id,
                    "version": version,
                },
                meter_update_params.MeterUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
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
    ) -> AsyncPaginator[MeterResponse, AsyncCursor[MeterResponse]]:
        """
        Retrieve a list of Meters that can be filtered by Product, Meter ID, or Meter
        short code.

        Args:
          codes: List of Meter codes to retrieve. These are the unique short codes that identify
              each Meter.

          ids: List of Meter IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of Meters to retrieve per page.

          product_id: The UUIDs of the Products to retrieve Meters for.

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
            f"/organizations/{org_id}/meters",
            page=AsyncCursor[MeterResponse],
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
                    meter_list_params.MeterListParams,
                ),
            ),
            model=MeterResponse,
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
    ) -> MeterResponse:
        """
        Delete the Meter with the given UUID.

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
            f"/organizations/{org_id}/meters/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeterResponse,
        )


class MetersResourceWithRawResponse:
    def __init__(self, meters: MetersResource) -> None:
        self._meters = meters

        self.create = to_raw_response_wrapper(
            meters.create,
        )
        self.retrieve = to_raw_response_wrapper(
            meters.retrieve,
        )
        self.update = to_raw_response_wrapper(
            meters.update,
        )
        self.list = to_raw_response_wrapper(
            meters.list,
        )
        self.delete = to_raw_response_wrapper(
            meters.delete,
        )


class AsyncMetersResourceWithRawResponse:
    def __init__(self, meters: AsyncMetersResource) -> None:
        self._meters = meters

        self.create = async_to_raw_response_wrapper(
            meters.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            meters.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            meters.update,
        )
        self.list = async_to_raw_response_wrapper(
            meters.list,
        )
        self.delete = async_to_raw_response_wrapper(
            meters.delete,
        )


class MetersResourceWithStreamingResponse:
    def __init__(self, meters: MetersResource) -> None:
        self._meters = meters

        self.create = to_streamed_response_wrapper(
            meters.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            meters.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            meters.update,
        )
        self.list = to_streamed_response_wrapper(
            meters.list,
        )
        self.delete = to_streamed_response_wrapper(
            meters.delete,
        )


class AsyncMetersResourceWithStreamingResponse:
    def __init__(self, meters: AsyncMetersResource) -> None:
        self._meters = meters

        self.create = async_to_streamed_response_wrapper(
            meters.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            meters.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            meters.update,
        )
        self.list = async_to_streamed_response_wrapper(
            meters.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            meters.delete,
        )
