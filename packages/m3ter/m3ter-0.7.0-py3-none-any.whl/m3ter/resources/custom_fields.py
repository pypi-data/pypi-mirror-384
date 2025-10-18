# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union

import httpx

from ..types import custom_field_update_params
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
from ..types.custom_fields_response import CustomFieldsResponse

__all__ = ["CustomFieldsResource", "AsyncCustomFieldsResource"]


class CustomFieldsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CustomFieldsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CustomFieldsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CustomFieldsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CustomFieldsResourceWithStreamingResponse(self)

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
    ) -> CustomFieldsResponse:
        """
        Retrieve all Custom Fields added at Organizational level for the entities that
        support them.

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
            f"/organizations/{org_id}/customfields",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomFieldsResponse,
        )

    def update(
        self,
        *,
        org_id: str | None = None,
        account: Dict[str, Union[str, float]] | Omit = omit,
        account_plan: Dict[str, Union[str, float]] | Omit = omit,
        aggregation: Dict[str, Union[str, float]] | Omit = omit,
        compound_aggregation: Dict[str, Union[str, float]] | Omit = omit,
        contract: Dict[str, Union[str, float]] | Omit = omit,
        meter: Dict[str, Union[str, float]] | Omit = omit,
        organization: Dict[str, Union[str, float]] | Omit = omit,
        plan: Dict[str, Union[str, float]] | Omit = omit,
        plan_template: Dict[str, Union[str, float]] | Omit = omit,
        product: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CustomFieldsResponse:
        """
        Update Custom Fields added at Organization level to entities that support them.

        Args:
          account: Updates to Account entity CustomFields.

          account_plan: Updates to AccountPlan entity CustomFields.

          aggregation: Updates to simple Aggregation entity CustomFields.

          compound_aggregation: Updates to Compound Aggregation entity CustomFields.

          contract: Updates to Contract entity CustomFields.

          meter: Updates to Meter entity CustomFields.

          organization: Updates to Organization CustomFields.

          plan: Updates to Plan entity CustomFields.

          plan_template: Updates to planTemplate entity CustomFields.

          product: Updates to Product entity CustomFields.

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
        return self._put(
            f"/organizations/{org_id}/customfields",
            body=maybe_transform(
                {
                    "account": account,
                    "account_plan": account_plan,
                    "aggregation": aggregation,
                    "compound_aggregation": compound_aggregation,
                    "contract": contract,
                    "meter": meter,
                    "organization": organization,
                    "plan": plan,
                    "plan_template": plan_template,
                    "product": product,
                    "version": version,
                },
                custom_field_update_params.CustomFieldUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomFieldsResponse,
        )


class AsyncCustomFieldsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCustomFieldsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCustomFieldsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCustomFieldsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCustomFieldsResourceWithStreamingResponse(self)

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
    ) -> CustomFieldsResponse:
        """
        Retrieve all Custom Fields added at Organizational level for the entities that
        support them.

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
            f"/organizations/{org_id}/customfields",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomFieldsResponse,
        )

    async def update(
        self,
        *,
        org_id: str | None = None,
        account: Dict[str, Union[str, float]] | Omit = omit,
        account_plan: Dict[str, Union[str, float]] | Omit = omit,
        aggregation: Dict[str, Union[str, float]] | Omit = omit,
        compound_aggregation: Dict[str, Union[str, float]] | Omit = omit,
        contract: Dict[str, Union[str, float]] | Omit = omit,
        meter: Dict[str, Union[str, float]] | Omit = omit,
        organization: Dict[str, Union[str, float]] | Omit = omit,
        plan: Dict[str, Union[str, float]] | Omit = omit,
        plan_template: Dict[str, Union[str, float]] | Omit = omit,
        product: Dict[str, Union[str, float]] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CustomFieldsResponse:
        """
        Update Custom Fields added at Organization level to entities that support them.

        Args:
          account: Updates to Account entity CustomFields.

          account_plan: Updates to AccountPlan entity CustomFields.

          aggregation: Updates to simple Aggregation entity CustomFields.

          compound_aggregation: Updates to Compound Aggregation entity CustomFields.

          contract: Updates to Contract entity CustomFields.

          meter: Updates to Meter entity CustomFields.

          organization: Updates to Organization CustomFields.

          plan: Updates to Plan entity CustomFields.

          plan_template: Updates to planTemplate entity CustomFields.

          product: Updates to Product entity CustomFields.

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
        return await self._put(
            f"/organizations/{org_id}/customfields",
            body=await async_maybe_transform(
                {
                    "account": account,
                    "account_plan": account_plan,
                    "aggregation": aggregation,
                    "compound_aggregation": compound_aggregation,
                    "contract": contract,
                    "meter": meter,
                    "organization": organization,
                    "plan": plan,
                    "plan_template": plan_template,
                    "product": product,
                    "version": version,
                },
                custom_field_update_params.CustomFieldUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CustomFieldsResponse,
        )


class CustomFieldsResourceWithRawResponse:
    def __init__(self, custom_fields: CustomFieldsResource) -> None:
        self._custom_fields = custom_fields

        self.retrieve = to_raw_response_wrapper(
            custom_fields.retrieve,
        )
        self.update = to_raw_response_wrapper(
            custom_fields.update,
        )


class AsyncCustomFieldsResourceWithRawResponse:
    def __init__(self, custom_fields: AsyncCustomFieldsResource) -> None:
        self._custom_fields = custom_fields

        self.retrieve = async_to_raw_response_wrapper(
            custom_fields.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            custom_fields.update,
        )


class CustomFieldsResourceWithStreamingResponse:
    def __init__(self, custom_fields: CustomFieldsResource) -> None:
        self._custom_fields = custom_fields

        self.retrieve = to_streamed_response_wrapper(
            custom_fields.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            custom_fields.update,
        )


class AsyncCustomFieldsResourceWithStreamingResponse:
    def __init__(self, custom_fields: AsyncCustomFieldsResource) -> None:
        self._custom_fields = custom_fields

        self.retrieve = async_to_streamed_response_wrapper(
            custom_fields.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            custom_fields.update,
        )
