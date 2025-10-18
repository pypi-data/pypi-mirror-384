# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union

import httpx

from ..types import plan_group_list_params, plan_group_create_params, plan_group_update_params
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
from ..types.plan_group_response import PlanGroupResponse

__all__ = ["PlanGroupsResource", "AsyncPlanGroupsResource"]


class PlanGroupsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PlanGroupsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PlanGroupsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PlanGroupsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PlanGroupsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        currency: str,
        name: str,
        account_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        standing_charge: float | Omit = omit,
        standing_charge_accounting_product_id: str | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupResponse:
        """Create a new PlanGroup.

        This endpoint creates a new PlanGroup within the
        specified organization.

        Args:
          currency: Currency code for the PlanGroup (For example, USD).

          name: The name of the PlanGroup.

          account_id: Optional. This PlanGroup is created as bespoke for the associated Account with
              this Account ID.

          code: The short code representing the PlanGroup.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The minimum spend amount for the PlanGroup.

          minimum_spend_accounting_product_id: Optional. Product ID to attribute the PlanGroup's minimum spend for accounting
              purposes.

          minimum_spend_bill_in_advance: A boolean flag that determines when the minimum spend is billed. This flag
              overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

              - **TRUE** - minimum spend is billed at the start of each billing period.
              - **FALSE** - minimum spend is billed at the end of each billing period.

          minimum_spend_description: Description of the minimum spend, displayed on the bill line item.

          standing_charge: Standing charge amount for the PlanGroup.

          standing_charge_accounting_product_id: Optional. Product ID to attribute the PlanGroup's standing charge for accounting
              purposes.

          standing_charge_bill_in_advance: A boolean flag that determines when the standing charge is billed. This flag
              overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

              - **TRUE** - standing charge is billed at the start of each billing period.
              - **FALSE** - standing charge is billed at the end of each billing period.

          standing_charge_description: Description of the standing charge, displayed on the bill line item.

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
            f"/organizations/{org_id}/plangroups",
            body=maybe_transform(
                {
                    "currency": currency,
                    "name": name,
                    "account_id": account_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_group_create_params.PlanGroupCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
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
    ) -> PlanGroupResponse:
        """
        Retrieve a specific PlanGroup with the given UUID.

        This endpoint retrieves detailed information about a specific PlanGroup
        identified by the given UUID within a specific organization.

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
            f"/organizations/{org_id}/plangroups/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        currency: str,
        name: str,
        account_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        standing_charge: float | Omit = omit,
        standing_charge_accounting_product_id: str | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupResponse:
        """
        Update the PlanGroup with the given UUID.

        This endpoint updates the details of a specific PlanGroup identified by the
        given UUID within a specific organization. This allows modifications to existing
        PlanGroup attributes.

        **Note:** If you have created Custom Fields for a PlanGroup, when you use this
        endpoint to update the PlanGroup use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          currency: Currency code for the PlanGroup (For example, USD).

          name: The name of the PlanGroup.

          account_id: Optional. This PlanGroup is created as bespoke for the associated Account with
              this Account ID.

          code: The short code representing the PlanGroup.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The minimum spend amount for the PlanGroup.

          minimum_spend_accounting_product_id: Optional. Product ID to attribute the PlanGroup's minimum spend for accounting
              purposes.

          minimum_spend_bill_in_advance: A boolean flag that determines when the minimum spend is billed. This flag
              overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

              - **TRUE** - minimum spend is billed at the start of each billing period.
              - **FALSE** - minimum spend is billed at the end of each billing period.

          minimum_spend_description: Description of the minimum spend, displayed on the bill line item.

          standing_charge: Standing charge amount for the PlanGroup.

          standing_charge_accounting_product_id: Optional. Product ID to attribute the PlanGroup's standing charge for accounting
              purposes.

          standing_charge_bill_in_advance: A boolean flag that determines when the standing charge is billed. This flag
              overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

              - **TRUE** - standing charge is billed at the start of each billing period.
              - **FALSE** - standing charge is billed at the end of each billing period.

          standing_charge_description: Description of the standing charge, displayed on the bill line item.

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
            f"/organizations/{org_id}/plangroups/{id}",
            body=maybe_transform(
                {
                    "currency": currency,
                    "name": name,
                    "account_id": account_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_group_update_params.PlanGroupUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[PlanGroupResponse]:
        """
        Retrieve a list of PlanGroups.

        Retrieves a list of PlanGroups within the specified organization. You can
        optionally filter by Account IDs or PlanGroup IDs, and also paginate the results
        for easier management.

        Args:
          account_id: Optional filter. The list of Account IDs to which the PlanGroups belong.

          ids: Optional filter. The list of PlanGroup IDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              PlanGroups in a paginated list.

          page_size: Specifies the maximum number of PlanGroups to retrieve per page.

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
            f"/organizations/{org_id}/plangroups",
            page=SyncCursor[PlanGroupResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    plan_group_list_params.PlanGroupListParams,
                ),
            ),
            model=PlanGroupResponse,
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
    ) -> PlanGroupResponse:
        """
        Delete a PlanGroup with the given UUID.

        This endpoint deletes the PlanGroup identified by the given UUID within a
        specific organization. This operation is irreversible and removes the PlanGroup
        along with any associated settings.

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
            f"/organizations/{org_id}/plangroups/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )


class AsyncPlanGroupsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPlanGroupsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPlanGroupsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPlanGroupsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPlanGroupsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        currency: str,
        name: str,
        account_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        standing_charge: float | Omit = omit,
        standing_charge_accounting_product_id: str | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupResponse:
        """Create a new PlanGroup.

        This endpoint creates a new PlanGroup within the
        specified organization.

        Args:
          currency: Currency code for the PlanGroup (For example, USD).

          name: The name of the PlanGroup.

          account_id: Optional. This PlanGroup is created as bespoke for the associated Account with
              this Account ID.

          code: The short code representing the PlanGroup.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The minimum spend amount for the PlanGroup.

          minimum_spend_accounting_product_id: Optional. Product ID to attribute the PlanGroup's minimum spend for accounting
              purposes.

          minimum_spend_bill_in_advance: A boolean flag that determines when the minimum spend is billed. This flag
              overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

              - **TRUE** - minimum spend is billed at the start of each billing period.
              - **FALSE** - minimum spend is billed at the end of each billing period.

          minimum_spend_description: Description of the minimum spend, displayed on the bill line item.

          standing_charge: Standing charge amount for the PlanGroup.

          standing_charge_accounting_product_id: Optional. Product ID to attribute the PlanGroup's standing charge for accounting
              purposes.

          standing_charge_bill_in_advance: A boolean flag that determines when the standing charge is billed. This flag
              overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

              - **TRUE** - standing charge is billed at the start of each billing period.
              - **FALSE** - standing charge is billed at the end of each billing period.

          standing_charge_description: Description of the standing charge, displayed on the bill line item.

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
            f"/organizations/{org_id}/plangroups",
            body=await async_maybe_transform(
                {
                    "currency": currency,
                    "name": name,
                    "account_id": account_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_group_create_params.PlanGroupCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
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
    ) -> PlanGroupResponse:
        """
        Retrieve a specific PlanGroup with the given UUID.

        This endpoint retrieves detailed information about a specific PlanGroup
        identified by the given UUID within a specific organization.

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
            f"/organizations/{org_id}/plangroups/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        currency: str,
        name: str,
        account_id: str | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        standing_charge: float | Omit = omit,
        standing_charge_accounting_product_id: str | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupResponse:
        """
        Update the PlanGroup with the given UUID.

        This endpoint updates the details of a specific PlanGroup identified by the
        given UUID within a specific organization. This allows modifications to existing
        PlanGroup attributes.

        **Note:** If you have created Custom Fields for a PlanGroup, when you use this
        endpoint to update the PlanGroup use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          currency: Currency code for the PlanGroup (For example, USD).

          name: The name of the PlanGroup.

          account_id: Optional. This PlanGroup is created as bespoke for the associated Account with
              this Account ID.

          code: The short code representing the PlanGroup.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The minimum spend amount for the PlanGroup.

          minimum_spend_accounting_product_id: Optional. Product ID to attribute the PlanGroup's minimum spend for accounting
              purposes.

          minimum_spend_bill_in_advance: A boolean flag that determines when the minimum spend is billed. This flag
              overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

              - **TRUE** - minimum spend is billed at the start of each billing period.
              - **FALSE** - minimum spend is billed at the end of each billing period.

          minimum_spend_description: Description of the minimum spend, displayed on the bill line item.

          standing_charge: Standing charge amount for the PlanGroup.

          standing_charge_accounting_product_id: Optional. Product ID to attribute the PlanGroup's standing charge for accounting
              purposes.

          standing_charge_bill_in_advance: A boolean flag that determines when the standing charge is billed. This flag
              overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

              - **TRUE** - standing charge is billed at the start of each billing period.
              - **FALSE** - standing charge is billed at the end of each billing period.

          standing_charge_description: Description of the standing charge, displayed on the bill line item.

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
            f"/organizations/{org_id}/plangroups/{id}",
            body=await async_maybe_transform(
                {
                    "currency": currency,
                    "name": name,
                    "account_id": account_id,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_group_update_params.PlanGroupUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[PlanGroupResponse, AsyncCursor[PlanGroupResponse]]:
        """
        Retrieve a list of PlanGroups.

        Retrieves a list of PlanGroups within the specified organization. You can
        optionally filter by Account IDs or PlanGroup IDs, and also paginate the results
        for easier management.

        Args:
          account_id: Optional filter. The list of Account IDs to which the PlanGroups belong.

          ids: Optional filter. The list of PlanGroup IDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              PlanGroups in a paginated list.

          page_size: Specifies the maximum number of PlanGroups to retrieve per page.

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
            f"/organizations/{org_id}/plangroups",
            page=AsyncCursor[PlanGroupResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    plan_group_list_params.PlanGroupListParams,
                ),
            ),
            model=PlanGroupResponse,
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
    ) -> PlanGroupResponse:
        """
        Delete a PlanGroup with the given UUID.

        This endpoint deletes the PlanGroup identified by the given UUID within a
        specific organization. This operation is irreversible and removes the PlanGroup
        along with any associated settings.

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
            f"/organizations/{org_id}/plangroups/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupResponse,
        )


class PlanGroupsResourceWithRawResponse:
    def __init__(self, plan_groups: PlanGroupsResource) -> None:
        self._plan_groups = plan_groups

        self.create = to_raw_response_wrapper(
            plan_groups.create,
        )
        self.retrieve = to_raw_response_wrapper(
            plan_groups.retrieve,
        )
        self.update = to_raw_response_wrapper(
            plan_groups.update,
        )
        self.list = to_raw_response_wrapper(
            plan_groups.list,
        )
        self.delete = to_raw_response_wrapper(
            plan_groups.delete,
        )


class AsyncPlanGroupsResourceWithRawResponse:
    def __init__(self, plan_groups: AsyncPlanGroupsResource) -> None:
        self._plan_groups = plan_groups

        self.create = async_to_raw_response_wrapper(
            plan_groups.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            plan_groups.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            plan_groups.update,
        )
        self.list = async_to_raw_response_wrapper(
            plan_groups.list,
        )
        self.delete = async_to_raw_response_wrapper(
            plan_groups.delete,
        )


class PlanGroupsResourceWithStreamingResponse:
    def __init__(self, plan_groups: PlanGroupsResource) -> None:
        self._plan_groups = plan_groups

        self.create = to_streamed_response_wrapper(
            plan_groups.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            plan_groups.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            plan_groups.update,
        )
        self.list = to_streamed_response_wrapper(
            plan_groups.list,
        )
        self.delete = to_streamed_response_wrapper(
            plan_groups.delete,
        )


class AsyncPlanGroupsResourceWithStreamingResponse:
    def __init__(self, plan_groups: AsyncPlanGroupsResource) -> None:
        self._plan_groups = plan_groups

        self.create = async_to_streamed_response_wrapper(
            plan_groups.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            plan_groups.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            plan_groups.update,
        )
        self.list = async_to_streamed_response_wrapper(
            plan_groups.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            plan_groups.delete,
        )
