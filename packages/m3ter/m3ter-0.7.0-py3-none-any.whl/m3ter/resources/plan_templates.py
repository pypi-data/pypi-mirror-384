# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union
from typing_extensions import Literal

import httpx

from ..types import plan_template_list_params, plan_template_create_params, plan_template_update_params
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
from ..types.plan_template_response import PlanTemplateResponse

__all__ = ["PlanTemplatesResource", "AsyncPlanTemplatesResource"]


class PlanTemplatesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PlanTemplatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PlanTemplatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PlanTemplatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PlanTemplatesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"],
        currency: str,
        name: str,
        product_id: str,
        standing_charge: float,
        bill_frequency_interval: int | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        standing_charge_interval: int | Omit = omit,
        standing_charge_offset: int | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanTemplateResponse:
        """
        Create a new PlanTemplate.

        This endpoint creates a new PlanTemplate within a specific Organization,
        identified by its unique UUID. The request body should contain the necessary
        information for the new PlanTemplate.

        Args:
          bill_frequency: Determines the frequency at which bills are generated.

              - **Daily**. Starting at midnight each day, covering the twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday, covering the seven-day period
                following.

              - **Monthly**. Starting at midnight on the first day of each month, covering the
                entire calendar month following.

              - **Annually**. Starting at midnight on first day of each year covering the
                entire calendar year following.

          currency: The ISO currency code for the currency used to charge end users - for example
              USD, GBP, EUR. This defines the _pricing currency_ and is inherited by any Plans
              based on the Plan Template.

              **Notes:**

              - You can define a currency at Organization-level or Account-level to be used as
                the _billing currency_. This can be a different currency to that used for the
                Plan as the _pricing currency_.
              - If the billing currency for an Account is different to the pricing currency
                used by a Plan attached to the Account, you must ensure a _currency conversion
                rate_ is defined for your Organization to convert the pricing currency into
                the billing currency at billing, otherwise Bills will fail for the Account.
              - To define any required currency conversion rates, use the
                `currencyConversions` request body parameter for the
                [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
                call.

          name: Descriptive name for the PlanTemplate.

          product_id: The unique identifier (UUID) of the Product associated with this PlanTemplate.

          standing_charge: The fixed charge _(standing charge)_ applied to customer bills. This charge is
              prorated and must be a non-negative number.

          bill_frequency_interval: How often bills are issued. For example, if `billFrequency` is Monthly and
              `billFrequencyInterval` is 3, bills are issued every three months.

          code: A unique, short code reference for the PlanTemplate. This code should not
              contain control characters or spaces.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The Product minimum spend amount per billing cycle for end customer Accounts on
              a pricing Plan based on the PlanTemplate. This must be a non-negative number.

          minimum_spend_bill_in_advance: A boolean that determines when the minimum spend is billed.

              - TRUE - minimum spend is billed at the start of each billing period.
              - FALSE - minimum spend is billed at the end of each billing period.

              Overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: The ranking of the PlanTemplate among your pricing plans. Lower numbers
              represent more basic plans, while higher numbers represent premium plans. This
              must be a non-negative integer.

              **NOTE: DEPRECATED** - do not use.

          standing_charge_bill_in_advance: A boolean that determines when the standing charge is billed.

              - TRUE - standing charge is billed at the start of each billing period.
              - FALSE - standing charge is billed at the end of each billing period.

              Overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

          standing_charge_interval: How often the standing charge is applied. For example, if the bill is issued
              every three months and `standingChargeInterval` is 2, then the standing charge
              is applied every six months.

          standing_charge_offset: Defines an offset for when the standing charge is first applied. For example, if
              the bill is issued every three months and the `standingChargeOfset` is 0, then
              the charge is applied to the first bill _(at three months)_; if 1, it would be
              applied to the second bill _(at six months)_, and so on.

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
            f"/organizations/{org_id}/plantemplates",
            body=maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "currency": currency,
                    "name": name,
                    "product_id": product_id,
                    "standing_charge": standing_charge,
                    "bill_frequency_interval": bill_frequency_interval,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "standing_charge_interval": standing_charge_interval,
                    "standing_charge_offset": standing_charge_offset,
                    "version": version,
                },
                plan_template_create_params.PlanTemplateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
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
    ) -> PlanTemplateResponse:
        """
        Retrieve a specific PlanTemplate.

        This endpoint allows you to retrieve a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/plantemplates/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"],
        currency: str,
        name: str,
        product_id: str,
        standing_charge: float,
        bill_frequency_interval: int | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        standing_charge_interval: int | Omit = omit,
        standing_charge_offset: int | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanTemplateResponse:
        """
        Update a specific PlanTemplate.

        This endpoint enables you to update a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs). The request
        body should contain the updated information for the PlanTemplate.

        **Note:** If you have created Custom Fields for a Plan Template, when you use
        this endpoint to update the Plan Template use the `customFields` parameter to
        preserve those Custom Fields. If you omit them from the update request, they
        will be lost.

        Args:
          bill_frequency: Determines the frequency at which bills are generated.

              - **Daily**. Starting at midnight each day, covering the twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday, covering the seven-day period
                following.

              - **Monthly**. Starting at midnight on the first day of each month, covering the
                entire calendar month following.

              - **Annually**. Starting at midnight on first day of each year covering the
                entire calendar year following.

          currency: The ISO currency code for the currency used to charge end users - for example
              USD, GBP, EUR. This defines the _pricing currency_ and is inherited by any Plans
              based on the Plan Template.

              **Notes:**

              - You can define a currency at Organization-level or Account-level to be used as
                the _billing currency_. This can be a different currency to that used for the
                Plan as the _pricing currency_.
              - If the billing currency for an Account is different to the pricing currency
                used by a Plan attached to the Account, you must ensure a _currency conversion
                rate_ is defined for your Organization to convert the pricing currency into
                the billing currency at billing, otherwise Bills will fail for the Account.
              - To define any required currency conversion rates, use the
                `currencyConversions` request body parameter for the
                [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
                call.

          name: Descriptive name for the PlanTemplate.

          product_id: The unique identifier (UUID) of the Product associated with this PlanTemplate.

          standing_charge: The fixed charge _(standing charge)_ applied to customer bills. This charge is
              prorated and must be a non-negative number.

          bill_frequency_interval: How often bills are issued. For example, if `billFrequency` is Monthly and
              `billFrequencyInterval` is 3, bills are issued every three months.

          code: A unique, short code reference for the PlanTemplate. This code should not
              contain control characters or spaces.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The Product minimum spend amount per billing cycle for end customer Accounts on
              a pricing Plan based on the PlanTemplate. This must be a non-negative number.

          minimum_spend_bill_in_advance: A boolean that determines when the minimum spend is billed.

              - TRUE - minimum spend is billed at the start of each billing period.
              - FALSE - minimum spend is billed at the end of each billing period.

              Overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: The ranking of the PlanTemplate among your pricing plans. Lower numbers
              represent more basic plans, while higher numbers represent premium plans. This
              must be a non-negative integer.

              **NOTE: DEPRECATED** - do not use.

          standing_charge_bill_in_advance: A boolean that determines when the standing charge is billed.

              - TRUE - standing charge is billed at the start of each billing period.
              - FALSE - standing charge is billed at the end of each billing period.

              Overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

          standing_charge_interval: How often the standing charge is applied. For example, if the bill is issued
              every three months and `standingChargeInterval` is 2, then the standing charge
              is applied every six months.

          standing_charge_offset: Defines an offset for when the standing charge is first applied. For example, if
              the bill is issued every three months and the `standingChargeOfset` is 0, then
              the charge is applied to the first bill _(at three months)_; if 1, it would be
              applied to the second bill _(at six months)_, and so on.

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
            f"/organizations/{org_id}/plantemplates/{id}",
            body=maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "currency": currency,
                    "name": name,
                    "product_id": product_id,
                    "standing_charge": standing_charge,
                    "bill_frequency_interval": bill_frequency_interval,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "standing_charge_interval": standing_charge_interval,
                    "standing_charge_offset": standing_charge_offset,
                    "version": version,
                },
                plan_template_update_params.PlanTemplateUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
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
    ) -> SyncCursor[PlanTemplateResponse]:
        """
        Retrieve a list of PlanTemplates.

        This endpoint enables you to retrieve a paginated list of PlanTemplates
        belonging to a specific Organization, identified by its UUID. You can filter the
        list by PlanTemplate IDs or Product IDs for more focused retrieval.

        Args:
          ids: List of specific PlanTemplate UUIDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              PlanTemplates in a paginated list.

          page_size: Specifies the maximum number of PlanTemplates to retrieve per page.

          product_id: The unique identifiers (UUIDs) of the Products to retrieve associated
              PlanTemplates.

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
            f"/organizations/{org_id}/plantemplates",
            page=SyncCursor[PlanTemplateResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    plan_template_list_params.PlanTemplateListParams,
                ),
            ),
            model=PlanTemplateResponse,
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
    ) -> PlanTemplateResponse:
        """
        Delete a specific PlanTemplate.

        This endpoint enables you to delete a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/plantemplates/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )


class AsyncPlanTemplatesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPlanTemplatesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPlanTemplatesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPlanTemplatesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPlanTemplatesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"],
        currency: str,
        name: str,
        product_id: str,
        standing_charge: float,
        bill_frequency_interval: int | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        standing_charge_interval: int | Omit = omit,
        standing_charge_offset: int | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanTemplateResponse:
        """
        Create a new PlanTemplate.

        This endpoint creates a new PlanTemplate within a specific Organization,
        identified by its unique UUID. The request body should contain the necessary
        information for the new PlanTemplate.

        Args:
          bill_frequency: Determines the frequency at which bills are generated.

              - **Daily**. Starting at midnight each day, covering the twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday, covering the seven-day period
                following.

              - **Monthly**. Starting at midnight on the first day of each month, covering the
                entire calendar month following.

              - **Annually**. Starting at midnight on first day of each year covering the
                entire calendar year following.

          currency: The ISO currency code for the currency used to charge end users - for example
              USD, GBP, EUR. This defines the _pricing currency_ and is inherited by any Plans
              based on the Plan Template.

              **Notes:**

              - You can define a currency at Organization-level or Account-level to be used as
                the _billing currency_. This can be a different currency to that used for the
                Plan as the _pricing currency_.
              - If the billing currency for an Account is different to the pricing currency
                used by a Plan attached to the Account, you must ensure a _currency conversion
                rate_ is defined for your Organization to convert the pricing currency into
                the billing currency at billing, otherwise Bills will fail for the Account.
              - To define any required currency conversion rates, use the
                `currencyConversions` request body parameter for the
                [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
                call.

          name: Descriptive name for the PlanTemplate.

          product_id: The unique identifier (UUID) of the Product associated with this PlanTemplate.

          standing_charge: The fixed charge _(standing charge)_ applied to customer bills. This charge is
              prorated and must be a non-negative number.

          bill_frequency_interval: How often bills are issued. For example, if `billFrequency` is Monthly and
              `billFrequencyInterval` is 3, bills are issued every three months.

          code: A unique, short code reference for the PlanTemplate. This code should not
              contain control characters or spaces.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The Product minimum spend amount per billing cycle for end customer Accounts on
              a pricing Plan based on the PlanTemplate. This must be a non-negative number.

          minimum_spend_bill_in_advance: A boolean that determines when the minimum spend is billed.

              - TRUE - minimum spend is billed at the start of each billing period.
              - FALSE - minimum spend is billed at the end of each billing period.

              Overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: The ranking of the PlanTemplate among your pricing plans. Lower numbers
              represent more basic plans, while higher numbers represent premium plans. This
              must be a non-negative integer.

              **NOTE: DEPRECATED** - do not use.

          standing_charge_bill_in_advance: A boolean that determines when the standing charge is billed.

              - TRUE - standing charge is billed at the start of each billing period.
              - FALSE - standing charge is billed at the end of each billing period.

              Overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

          standing_charge_interval: How often the standing charge is applied. For example, if the bill is issued
              every three months and `standingChargeInterval` is 2, then the standing charge
              is applied every six months.

          standing_charge_offset: Defines an offset for when the standing charge is first applied. For example, if
              the bill is issued every three months and the `standingChargeOfset` is 0, then
              the charge is applied to the first bill _(at three months)_; if 1, it would be
              applied to the second bill _(at six months)_, and so on.

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
            f"/organizations/{org_id}/plantemplates",
            body=await async_maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "currency": currency,
                    "name": name,
                    "product_id": product_id,
                    "standing_charge": standing_charge,
                    "bill_frequency_interval": bill_frequency_interval,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "standing_charge_interval": standing_charge_interval,
                    "standing_charge_offset": standing_charge_offset,
                    "version": version,
                },
                plan_template_create_params.PlanTemplateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
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
    ) -> PlanTemplateResponse:
        """
        Retrieve a specific PlanTemplate.

        This endpoint allows you to retrieve a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/plantemplates/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        bill_frequency: Literal["DAILY", "WEEKLY", "MONTHLY", "ANNUALLY", "AD_HOC", "MIXED"],
        currency: str,
        name: str,
        product_id: str,
        standing_charge: float,
        bill_frequency_interval: int | Omit = omit,
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        ordinal: int | Omit = omit,
        standing_charge_bill_in_advance: bool | Omit = omit,
        standing_charge_description: str | Omit = omit,
        standing_charge_interval: int | Omit = omit,
        standing_charge_offset: int | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanTemplateResponse:
        """
        Update a specific PlanTemplate.

        This endpoint enables you to update a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs). The request
        body should contain the updated information for the PlanTemplate.

        **Note:** If you have created Custom Fields for a Plan Template, when you use
        this endpoint to update the Plan Template use the `customFields` parameter to
        preserve those Custom Fields. If you omit them from the update request, they
        will be lost.

        Args:
          bill_frequency: Determines the frequency at which bills are generated.

              - **Daily**. Starting at midnight each day, covering the twenty-four hour period
                following.

              - **Weekly**. Starting at midnight on a Monday, covering the seven-day period
                following.

              - **Monthly**. Starting at midnight on the first day of each month, covering the
                entire calendar month following.

              - **Annually**. Starting at midnight on first day of each year covering the
                entire calendar year following.

          currency: The ISO currency code for the currency used to charge end users - for example
              USD, GBP, EUR. This defines the _pricing currency_ and is inherited by any Plans
              based on the Plan Template.

              **Notes:**

              - You can define a currency at Organization-level or Account-level to be used as
                the _billing currency_. This can be a different currency to that used for the
                Plan as the _pricing currency_.
              - If the billing currency for an Account is different to the pricing currency
                used by a Plan attached to the Account, you must ensure a _currency conversion
                rate_ is defined for your Organization to convert the pricing currency into
                the billing currency at billing, otherwise Bills will fail for the Account.
              - To define any required currency conversion rates, use the
                `currencyConversions` request body parameter for the
                [Update OrganizationConfig](https://www.m3ter.com/docs/api#tag/OrganizationConfig/operation/UpdateOrganizationConfig)
                call.

          name: Descriptive name for the PlanTemplate.

          product_id: The unique identifier (UUID) of the Product associated with this PlanTemplate.

          standing_charge: The fixed charge _(standing charge)_ applied to customer bills. This charge is
              prorated and must be a non-negative number.

          bill_frequency_interval: How often bills are issued. For example, if `billFrequency` is Monthly and
              `billFrequencyInterval` is 3, bills are issued every three months.

          code: A unique, short code reference for the PlanTemplate. This code should not
              contain control characters or spaces.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          minimum_spend: The Product minimum spend amount per billing cycle for end customer Accounts on
              a pricing Plan based on the PlanTemplate. This must be a non-negative number.

          minimum_spend_bill_in_advance: A boolean that determines when the minimum spend is billed.

              - TRUE - minimum spend is billed at the start of each billing period.
              - FALSE - minimum spend is billed at the end of each billing period.

              Overrides the setting at Organizational level for minimum spend billing in
              arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          ordinal: The ranking of the PlanTemplate among your pricing plans. Lower numbers
              represent more basic plans, while higher numbers represent premium plans. This
              must be a non-negative integer.

              **NOTE: DEPRECATED** - do not use.

          standing_charge_bill_in_advance: A boolean that determines when the standing charge is billed.

              - TRUE - standing charge is billed at the start of each billing period.
              - FALSE - standing charge is billed at the end of each billing period.

              Overrides the setting at Organizational level for standing charge billing in
              arrears/in advance.

          standing_charge_description: Standing charge description _(displayed on the bill line item)_.

          standing_charge_interval: How often the standing charge is applied. For example, if the bill is issued
              every three months and `standingChargeInterval` is 2, then the standing charge
              is applied every six months.

          standing_charge_offset: Defines an offset for when the standing charge is first applied. For example, if
              the bill is issued every three months and the `standingChargeOfset` is 0, then
              the charge is applied to the first bill _(at three months)_; if 1, it would be
              applied to the second bill _(at six months)_, and so on.

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
            f"/organizations/{org_id}/plantemplates/{id}",
            body=await async_maybe_transform(
                {
                    "bill_frequency": bill_frequency,
                    "currency": currency,
                    "name": name,
                    "product_id": product_id,
                    "standing_charge": standing_charge,
                    "bill_frequency_interval": bill_frequency_interval,
                    "code": code,
                    "custom_fields": custom_fields,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "ordinal": ordinal,
                    "standing_charge_bill_in_advance": standing_charge_bill_in_advance,
                    "standing_charge_description": standing_charge_description,
                    "standing_charge_interval": standing_charge_interval,
                    "standing_charge_offset": standing_charge_offset,
                    "version": version,
                },
                plan_template_update_params.PlanTemplateUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
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
    ) -> AsyncPaginator[PlanTemplateResponse, AsyncCursor[PlanTemplateResponse]]:
        """
        Retrieve a list of PlanTemplates.

        This endpoint enables you to retrieve a paginated list of PlanTemplates
        belonging to a specific Organization, identified by its UUID. You can filter the
        list by PlanTemplate IDs or Product IDs for more focused retrieval.

        Args:
          ids: List of specific PlanTemplate UUIDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              PlanTemplates in a paginated list.

          page_size: Specifies the maximum number of PlanTemplates to retrieve per page.

          product_id: The unique identifiers (UUIDs) of the Products to retrieve associated
              PlanTemplates.

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
            f"/organizations/{org_id}/plantemplates",
            page=AsyncCursor[PlanTemplateResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    plan_template_list_params.PlanTemplateListParams,
                ),
            ),
            model=PlanTemplateResponse,
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
    ) -> PlanTemplateResponse:
        """
        Delete a specific PlanTemplate.

        This endpoint enables you to delete a specific PlanTemplate within a specific
        Organization, both identified by their unique identifiers (UUIDs).

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
            f"/organizations/{org_id}/plantemplates/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanTemplateResponse,
        )


class PlanTemplatesResourceWithRawResponse:
    def __init__(self, plan_templates: PlanTemplatesResource) -> None:
        self._plan_templates = plan_templates

        self.create = to_raw_response_wrapper(
            plan_templates.create,
        )
        self.retrieve = to_raw_response_wrapper(
            plan_templates.retrieve,
        )
        self.update = to_raw_response_wrapper(
            plan_templates.update,
        )
        self.list = to_raw_response_wrapper(
            plan_templates.list,
        )
        self.delete = to_raw_response_wrapper(
            plan_templates.delete,
        )


class AsyncPlanTemplatesResourceWithRawResponse:
    def __init__(self, plan_templates: AsyncPlanTemplatesResource) -> None:
        self._plan_templates = plan_templates

        self.create = async_to_raw_response_wrapper(
            plan_templates.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            plan_templates.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            plan_templates.update,
        )
        self.list = async_to_raw_response_wrapper(
            plan_templates.list,
        )
        self.delete = async_to_raw_response_wrapper(
            plan_templates.delete,
        )


class PlanTemplatesResourceWithStreamingResponse:
    def __init__(self, plan_templates: PlanTemplatesResource) -> None:
        self._plan_templates = plan_templates

        self.create = to_streamed_response_wrapper(
            plan_templates.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            plan_templates.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            plan_templates.update,
        )
        self.list = to_streamed_response_wrapper(
            plan_templates.list,
        )
        self.delete = to_streamed_response_wrapper(
            plan_templates.delete,
        )


class AsyncPlanTemplatesResourceWithStreamingResponse:
    def __init__(self, plan_templates: AsyncPlanTemplatesResource) -> None:
        self._plan_templates = plan_templates

        self.create = async_to_streamed_response_wrapper(
            plan_templates.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            plan_templates.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            plan_templates.update,
        )
        self.list = async_to_streamed_response_wrapper(
            plan_templates.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            plan_templates.delete,
        )
