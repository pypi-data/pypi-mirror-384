# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union

import httpx

from ..types import plan_list_params, plan_create_params, plan_update_params
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
from ..types.plan_response import PlanResponse

__all__ = ["PlansResource", "AsyncPlansResource"]


class PlansResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PlansResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PlansResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PlansResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PlansResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        plan_template_id: str,
        account_id: str | Omit = omit,
        bespoke: bool | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
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
    ) -> PlanResponse:
        """
        Create a new Plan.

        Args:
          code: Unique short code reference for the Plan.

          name: Descriptive name for the Plan.

          plan_template_id: UUID of the PlanTemplate the Plan belongs to.

          account_id: _(Optional)_. Used to specify an Account for which the Plan will be a
              custom/bespoke Plan:

              - Use when first creating a Plan.
              - A custom/bespoke Plan can only be attached to the specified Account.
              - Once created, a custom/bespoke Plan cannot be updated to be made a
                custom/bespoke Plan for a different Account.

          bespoke: TRUE/FALSE flag indicating whether the plan is a custom/bespoke Plan for a
              particular Account:

              - When creating a Plan, use the `accountId` request parameter to specify the
                Account for which the Plan will be custom/bespoke.
              - A custom/bespoke Plan can only be attached to the specified Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The product minimum spend amount per billing cycle for end customer Accounts on
              a priced Plan.

              _(Optional)_. Overrides PlanTemplate value.

          minimum_spend_accounting_product_id: Optional Product ID this plan's minimum spend should be attributed to for
              accounting purposes

          minimum_spend_bill_in_advance: When TRUE, minimum spend is billed at the start of each billing period.

              When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: Assigns a rank or position to the Plan in your order of pricing plans - lower
              numbers represent more basic pricing plans; higher numbers represent more
              premium pricing plans.

              _(Optional)_. Overrides PlanTemplate value.

              **NOTE: DEPRECATED** - do not use.

          standing_charge: The standing charge applied to bills for end customers. This is prorated.

              _(Optional)_. Overrides PlanTemplate value.

          standing_charge_accounting_product_id: Optional Product ID this plan's standing charge should be attributed to for
              accounting purposes

          standing_charge_bill_in_advance: When TRUE, standing charge is billed at the start of each billing period.

              When FALSE, standing charge is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
              billing in arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

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
            f"/organizations/{org_id}/plans",
            body=maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "plan_template_id": plan_template_id,
                    "account_id": account_id,
                    "bespoke": bespoke,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_create_params.PlanCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
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
    ) -> PlanResponse:
        """
        Retrieve the Plan with the given UUID.

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
            f"/organizations/{org_id}/plans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        plan_template_id: str,
        account_id: str | Omit = omit,
        bespoke: bool | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
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
    ) -> PlanResponse:
        """
        Update the Plan with the given UUID.

        **Note:** If you have created Custom Fields for a Plan, when you use this
        endpoint to update the Plan use the `customFields` parameter to preserve those
        Custom Fields. If you omit them from the update request, they will be lost.

        Args:
          code: Unique short code reference for the Plan.

          name: Descriptive name for the Plan.

          plan_template_id: UUID of the PlanTemplate the Plan belongs to.

          account_id: _(Optional)_. Used to specify an Account for which the Plan will be a
              custom/bespoke Plan:

              - Use when first creating a Plan.
              - A custom/bespoke Plan can only be attached to the specified Account.
              - Once created, a custom/bespoke Plan cannot be updated to be made a
                custom/bespoke Plan for a different Account.

          bespoke: TRUE/FALSE flag indicating whether the plan is a custom/bespoke Plan for a
              particular Account:

              - When creating a Plan, use the `accountId` request parameter to specify the
                Account for which the Plan will be custom/bespoke.
              - A custom/bespoke Plan can only be attached to the specified Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The product minimum spend amount per billing cycle for end customer Accounts on
              a priced Plan.

              _(Optional)_. Overrides PlanTemplate value.

          minimum_spend_accounting_product_id: Optional Product ID this plan's minimum spend should be attributed to for
              accounting purposes

          minimum_spend_bill_in_advance: When TRUE, minimum spend is billed at the start of each billing period.

              When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: Assigns a rank or position to the Plan in your order of pricing plans - lower
              numbers represent more basic pricing plans; higher numbers represent more
              premium pricing plans.

              _(Optional)_. Overrides PlanTemplate value.

              **NOTE: DEPRECATED** - do not use.

          standing_charge: The standing charge applied to bills for end customers. This is prorated.

              _(Optional)_. Overrides PlanTemplate value.

          standing_charge_accounting_product_id: Optional Product ID this plan's standing charge should be attributed to for
              accounting purposes

          standing_charge_bill_in_advance: When TRUE, standing charge is billed at the start of each billing period.

              When FALSE, standing charge is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
              billing in arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

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
            f"/organizations/{org_id}/plans/{id}",
            body=maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "plan_template_id": plan_template_id,
                    "account_id": account_id,
                    "bespoke": bespoke,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_update_params.PlanUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        product_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[PlanResponse]:
        """
        Retrieve a list of Plans that can be filtered by Product, Account, or Plan ID.

        Args:
          account_id: List of Account IDs the Plan belongs to.

          ids: List of Plan IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Plans to retrieve per page.

          product_id: UUID of the Product to retrieve Plans for.

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
            f"/organizations/{org_id}/plans",
            page=SyncCursor[PlanResponse],
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
                        "product_id": product_id,
                    },
                    plan_list_params.PlanListParams,
                ),
            ),
            model=PlanResponse,
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
    ) -> PlanResponse:
        """
        Delete the Plan with the given UUID.

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
            f"/organizations/{org_id}/plans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )


class AsyncPlansResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPlansResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPlansResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPlansResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPlansResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        plan_template_id: str,
        account_id: str | Omit = omit,
        bespoke: bool | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
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
    ) -> PlanResponse:
        """
        Create a new Plan.

        Args:
          code: Unique short code reference for the Plan.

          name: Descriptive name for the Plan.

          plan_template_id: UUID of the PlanTemplate the Plan belongs to.

          account_id: _(Optional)_. Used to specify an Account for which the Plan will be a
              custom/bespoke Plan:

              - Use when first creating a Plan.
              - A custom/bespoke Plan can only be attached to the specified Account.
              - Once created, a custom/bespoke Plan cannot be updated to be made a
                custom/bespoke Plan for a different Account.

          bespoke: TRUE/FALSE flag indicating whether the plan is a custom/bespoke Plan for a
              particular Account:

              - When creating a Plan, use the `accountId` request parameter to specify the
                Account for which the Plan will be custom/bespoke.
              - A custom/bespoke Plan can only be attached to the specified Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The product minimum spend amount per billing cycle for end customer Accounts on
              a priced Plan.

              _(Optional)_. Overrides PlanTemplate value.

          minimum_spend_accounting_product_id: Optional Product ID this plan's minimum spend should be attributed to for
              accounting purposes

          minimum_spend_bill_in_advance: When TRUE, minimum spend is billed at the start of each billing period.

              When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: Assigns a rank or position to the Plan in your order of pricing plans - lower
              numbers represent more basic pricing plans; higher numbers represent more
              premium pricing plans.

              _(Optional)_. Overrides PlanTemplate value.

              **NOTE: DEPRECATED** - do not use.

          standing_charge: The standing charge applied to bills for end customers. This is prorated.

              _(Optional)_. Overrides PlanTemplate value.

          standing_charge_accounting_product_id: Optional Product ID this plan's standing charge should be attributed to for
              accounting purposes

          standing_charge_bill_in_advance: When TRUE, standing charge is billed at the start of each billing period.

              When FALSE, standing charge is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
              billing in arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

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
            f"/organizations/{org_id}/plans",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "plan_template_id": plan_template_id,
                    "account_id": account_id,
                    "bespoke": bespoke,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_create_params.PlanCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
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
    ) -> PlanResponse:
        """
        Retrieve the Plan with the given UUID.

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
            f"/organizations/{org_id}/plans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        name: str,
        plan_template_id: str,
        account_id: str | Omit = omit,
        bespoke: bool | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_accounting_product_id: str | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
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
    ) -> PlanResponse:
        """
        Update the Plan with the given UUID.

        **Note:** If you have created Custom Fields for a Plan, when you use this
        endpoint to update the Plan use the `customFields` parameter to preserve those
        Custom Fields. If you omit them from the update request, they will be lost.

        Args:
          code: Unique short code reference for the Plan.

          name: Descriptive name for the Plan.

          plan_template_id: UUID of the PlanTemplate the Plan belongs to.

          account_id: _(Optional)_. Used to specify an Account for which the Plan will be a
              custom/bespoke Plan:

              - Use when first creating a Plan.
              - A custom/bespoke Plan can only be attached to the specified Account.
              - Once created, a custom/bespoke Plan cannot be updated to be made a
                custom/bespoke Plan for a different Account.

          bespoke: TRUE/FALSE flag indicating whether the plan is a custom/bespoke Plan for a
              particular Account:

              - When creating a Plan, use the `accountId` request parameter to specify the
                Account for which the Plan will be custom/bespoke.
              - A custom/bespoke Plan can only be attached to the specified Account.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The product minimum spend amount per billing cycle for end customer Accounts on
              a priced Plan.

              _(Optional)_. Overrides PlanTemplate value.

          minimum_spend_accounting_product_id: Optional Product ID this plan's minimum spend should be attributed to for
              accounting purposes

          minimum_spend_bill_in_advance: When TRUE, minimum spend is billed at the start of each billing period.

              When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: Assigns a rank or position to the Plan in your order of pricing plans - lower
              numbers represent more basic pricing plans; higher numbers represent more
              premium pricing plans.

              _(Optional)_. Overrides PlanTemplate value.

              **NOTE: DEPRECATED** - do not use.

          standing_charge: The standing charge applied to bills for end customers. This is prorated.

              _(Optional)_. Overrides PlanTemplate value.

          standing_charge_accounting_product_id: Optional Product ID this plan's standing charge should be attributed to for
              accounting purposes

          standing_charge_bill_in_advance: When TRUE, standing charge is billed at the start of each billing period.

              When FALSE, standing charge is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at PlanTemplate level for standing charge
              billing in arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

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
            f"/organizations/{org_id}/plans/{id}",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "name": name,
                    "plan_template_id": plan_template_id,
                    "account_id": account_id,
                    "bespoke": bespoke,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_accounting_product_id": minimum_spend_accounting_product_id,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge": standing_charge,
                    "standing_charge_accounting_product_id": standing_charge_accounting_product_id,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "version": version,
                },
                plan_update_params.PlanUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        product_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[PlanResponse, AsyncCursor[PlanResponse]]:
        """
        Retrieve a list of Plans that can be filtered by Product, Account, or Plan ID.

        Args:
          account_id: List of Account IDs the Plan belongs to.

          ids: List of Plan IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Plans to retrieve per page.

          product_id: UUID of the Product to retrieve Plans for.

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
            f"/organizations/{org_id}/plans",
            page=AsyncCursor[PlanResponse],
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
                        "product_id": product_id,
                    },
                    plan_list_params.PlanListParams,
                ),
            ),
            model=PlanResponse,
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
    ) -> PlanResponse:
        """
        Delete the Plan with the given UUID.

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
            f"/organizations/{org_id}/plans/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanResponse,
        )


class PlansResourceWithRawResponse:
    def __init__(self, plans: PlansResource) -> None:
        self._plans = plans

        self.create = to_raw_response_wrapper(
            plans.create,
        )
        self.retrieve = to_raw_response_wrapper(
            plans.retrieve,
        )
        self.update = to_raw_response_wrapper(
            plans.update,
        )
        self.list = to_raw_response_wrapper(
            plans.list,
        )
        self.delete = to_raw_response_wrapper(
            plans.delete,
        )


class AsyncPlansResourceWithRawResponse:
    def __init__(self, plans: AsyncPlansResource) -> None:
        self._plans = plans

        self.create = async_to_raw_response_wrapper(
            plans.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            plans.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            plans.update,
        )
        self.list = async_to_raw_response_wrapper(
            plans.list,
        )
        self.delete = async_to_raw_response_wrapper(
            plans.delete,
        )


class PlansResourceWithStreamingResponse:
    def __init__(self, plans: PlansResource) -> None:
        self._plans = plans

        self.create = to_streamed_response_wrapper(
            plans.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            plans.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            plans.update,
        )
        self.list = to_streamed_response_wrapper(
            plans.list,
        )
        self.delete = to_streamed_response_wrapper(
            plans.delete,
        )


class AsyncPlansResourceWithStreamingResponse:
    def __init__(self, plans: AsyncPlansResource) -> None:
        self._plans = plans

        self.create = async_to_streamed_response_wrapper(
            plans.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            plans.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            plans.update,
        )
        self.list = async_to_streamed_response_wrapper(
            plans.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            plans.delete,
        )
