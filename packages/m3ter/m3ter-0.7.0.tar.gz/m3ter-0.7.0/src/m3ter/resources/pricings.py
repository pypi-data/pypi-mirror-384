# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import datetime
from typing_extensions import Literal

import httpx

from ..types import pricing_list_params, pricing_create_params, pricing_update_params
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
from ..types.pricing_response import PricingResponse
from ..types.shared_params.pricing_band import PricingBand

__all__ = ["PricingsResource", "AsyncPricingsResource"]


class PricingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PricingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PricingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PricingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PricingsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        aggregation_id: str | Omit = omit,
        code: str | Omit = omit,
        compound_aggregation_id: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        overage_pricing_bands: Iterable[PricingBand] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        segment: Dict[str, str] | Omit = omit,
        tiers_span_plan: bool | Omit = omit,
        type: Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PricingResponse:
        """
        Create a new Pricing.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          aggregation_id: UUID of the Aggregation used to create the Pricing. Use this when creating a
              Pricing for a segmented aggregation.

          code: Unique short code for the Pricing.

          compound_aggregation_id: UUID of the Compound Aggregation used to create the Pricing.

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

          minimum_spend: The minimum spend amount per billing cycle for end customer Accounts on a Plan
              to which the Pricing is applied.

          minimum_spend_bill_in_advance: The default value is **FALSE**.

              - When TRUE, minimum spend is billed at the start of each billing period.

              - When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at Organization level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          overage_pricing_bands: Specify Prepayment/Balance overage pricing in pricing bands for the case of a
              **Tiered** pricing structure.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          segment: Specifies the segment value which you are defining a Pricing for using this
              call:

              - For each segment value defined on a Segmented Aggregation you must create a
                separate Pricing and use the appropriate `aggregationId` parameter for the
                call.
              - If you specify a segment value that has not been defined for the Aggregation,
                you'll receive an error.
              - If you've defined segment values for the Aggregation using a single wildcard
                or multiple wildcards, you can create Pricing for these wildcard segment
                values also.

              For more details on creating Pricings for segment values on a Segmented
              Aggregation using this call, together with some examples, see the
              [Using API Call to Create Segmented Pricings](https://www.m3ter.com/docs/guides/plans-and-pricing/pricing-plans/pricing-plans-using-segmented-aggregations#using-api-call-to-create-a-segmented-pricing)
              in our User Documentation.

          tiers_span_plan: The default value is **FALSE**.

              - If TRUE, usage accumulates over the entire period the priced Plan is active
                for the account, and is not reset for pricing band rates at the start of each
                billing period.

              - If FALSE, usage does not accumulate, and is reset for pricing bands at the
                start of each billing period.

          type: - **DEBIT**. Default setting. The amount calculated using the Pricing is added
                to the bill as a debit.

              - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the same Product.

              - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the entire bill, which
                might include other Products the Account consumes.

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
            f"/organizations/{org_id}/pricings",
            body=maybe_transform(
                {
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "aggregation_id": aggregation_id,
                    "code": code,
                    "compound_aggregation_id": compound_aggregation_id,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "overage_pricing_bands": overage_pricing_bands,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "segment": segment,
                    "tiers_span_plan": tiers_span_plan,
                    "type": type,
                    "version": version,
                },
                pricing_create_params.PricingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
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
    ) -> PricingResponse:
        """
        Retrieve the Pricing with the given UUID.

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
            f"/organizations/{org_id}/pricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        aggregation_id: str | Omit = omit,
        code: str | Omit = omit,
        compound_aggregation_id: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        overage_pricing_bands: Iterable[PricingBand] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        segment: Dict[str, str] | Omit = omit,
        tiers_span_plan: bool | Omit = omit,
        type: Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PricingResponse:
        """
        Update Pricing for the given UUID.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          aggregation_id: UUID of the Aggregation used to create the Pricing. Use this when creating a
              Pricing for a segmented aggregation.

          code: Unique short code for the Pricing.

          compound_aggregation_id: UUID of the Compound Aggregation used to create the Pricing.

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

          minimum_spend: The minimum spend amount per billing cycle for end customer Accounts on a Plan
              to which the Pricing is applied.

          minimum_spend_bill_in_advance: The default value is **FALSE**.

              - When TRUE, minimum spend is billed at the start of each billing period.

              - When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at Organization level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          overage_pricing_bands: Specify Prepayment/Balance overage pricing in pricing bands for the case of a
              **Tiered** pricing structure.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          segment: Specifies the segment value which you are defining a Pricing for using this
              call:

              - For each segment value defined on a Segmented Aggregation you must create a
                separate Pricing and use the appropriate `aggregationId` parameter for the
                call.
              - If you specify a segment value that has not been defined for the Aggregation,
                you'll receive an error.
              - If you've defined segment values for the Aggregation using a single wildcard
                or multiple wildcards, you can create Pricing for these wildcard segment
                values also.

              For more details on creating Pricings for segment values on a Segmented
              Aggregation using this call, together with some examples, see the
              [Using API Call to Create Segmented Pricings](https://www.m3ter.com/docs/guides/plans-and-pricing/pricing-plans/pricing-plans-using-segmented-aggregations#using-api-call-to-create-a-segmented-pricing)
              in our User Documentation.

          tiers_span_plan: The default value is **FALSE**.

              - If TRUE, usage accumulates over the entire period the priced Plan is active
                for the account, and is not reset for pricing band rates at the start of each
                billing period.

              - If FALSE, usage does not accumulate, and is reset for pricing bands at the
                start of each billing period.

          type: - **DEBIT**. Default setting. The amount calculated using the Pricing is added
                to the bill as a debit.

              - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the same Product.

              - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the entire bill, which
                might include other Products the Account consumes.

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
            f"/organizations/{org_id}/pricings/{id}",
            body=maybe_transform(
                {
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "aggregation_id": aggregation_id,
                    "code": code,
                    "compound_aggregation_id": compound_aggregation_id,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "overage_pricing_bands": overage_pricing_bands,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "segment": segment,
                    "tiers_span_plan": tiers_span_plan,
                    "type": type,
                    "version": version,
                },
                pricing_update_params.PricingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        aggregation_id: str | Omit = omit,
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
    ) -> SyncCursor[PricingResponse]:
        """
        Retrieve a list of Pricings filtered by date, Plan ID, PlanTemplate ID, or
        Pricing ID.

        Args:
          aggregation_id: UUID of the Aggregation to retrieve pricings for

          date: Date on which to retrieve active Pricings.

          ids: List of Pricing IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Pricings to retrieve per page.

          plan_id: UUID of the Plan to retrieve Pricings for.

          plan_template_id: UUID of the PlanTemplate to retrieve Pricings for.

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
            f"/organizations/{org_id}/pricings",
            page=SyncCursor[PricingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "aggregation_id": aggregation_id,
                        "date": date,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan_id": plan_id,
                        "plan_template_id": plan_template_id,
                    },
                    pricing_list_params.PricingListParams,
                ),
            ),
            model=PricingResponse,
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
    ) -> PricingResponse:
        """
        Delete the Pricing with the given UUID.

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
            f"/organizations/{org_id}/pricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )


class AsyncPricingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPricingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPricingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPricingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPricingsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        aggregation_id: str | Omit = omit,
        code: str | Omit = omit,
        compound_aggregation_id: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        overage_pricing_bands: Iterable[PricingBand] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        segment: Dict[str, str] | Omit = omit,
        tiers_span_plan: bool | Omit = omit,
        type: Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PricingResponse:
        """
        Create a new Pricing.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          aggregation_id: UUID of the Aggregation used to create the Pricing. Use this when creating a
              Pricing for a segmented aggregation.

          code: Unique short code for the Pricing.

          compound_aggregation_id: UUID of the Compound Aggregation used to create the Pricing.

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

          minimum_spend: The minimum spend amount per billing cycle for end customer Accounts on a Plan
              to which the Pricing is applied.

          minimum_spend_bill_in_advance: The default value is **FALSE**.

              - When TRUE, minimum spend is billed at the start of each billing period.

              - When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at Organization level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          overage_pricing_bands: Specify Prepayment/Balance overage pricing in pricing bands for the case of a
              **Tiered** pricing structure.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          segment: Specifies the segment value which you are defining a Pricing for using this
              call:

              - For each segment value defined on a Segmented Aggregation you must create a
                separate Pricing and use the appropriate `aggregationId` parameter for the
                call.
              - If you specify a segment value that has not been defined for the Aggregation,
                you'll receive an error.
              - If you've defined segment values for the Aggregation using a single wildcard
                or multiple wildcards, you can create Pricing for these wildcard segment
                values also.

              For more details on creating Pricings for segment values on a Segmented
              Aggregation using this call, together with some examples, see the
              [Using API Call to Create Segmented Pricings](https://www.m3ter.com/docs/guides/plans-and-pricing/pricing-plans/pricing-plans-using-segmented-aggregations#using-api-call-to-create-a-segmented-pricing)
              in our User Documentation.

          tiers_span_plan: The default value is **FALSE**.

              - If TRUE, usage accumulates over the entire period the priced Plan is active
                for the account, and is not reset for pricing band rates at the start of each
                billing period.

              - If FALSE, usage does not accumulate, and is reset for pricing bands at the
                start of each billing period.

          type: - **DEBIT**. Default setting. The amount calculated using the Pricing is added
                to the bill as a debit.

              - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the same Product.

              - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the entire bill, which
                might include other Products the Account consumes.

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
            f"/organizations/{org_id}/pricings",
            body=await async_maybe_transform(
                {
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "aggregation_id": aggregation_id,
                    "code": code,
                    "compound_aggregation_id": compound_aggregation_id,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "overage_pricing_bands": overage_pricing_bands,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "segment": segment,
                    "tiers_span_plan": tiers_span_plan,
                    "type": type,
                    "version": version,
                },
                pricing_create_params.PricingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
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
    ) -> PricingResponse:
        """
        Retrieve the Pricing with the given UUID.

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
            f"/organizations/{org_id}/pricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        pricing_bands: Iterable[PricingBand],
        start_date: Union[str, datetime],
        accounting_product_id: str | Omit = omit,
        aggregation_id: str | Omit = omit,
        code: str | Omit = omit,
        compound_aggregation_id: str | Omit = omit,
        cumulative: bool | Omit = omit,
        description: str | Omit = omit,
        end_date: Union[str, datetime] | Omit = omit,
        minimum_spend: float | Omit = omit,
        minimum_spend_bill_in_advance: bool | Omit = omit,
        minimum_spend_description: str | Omit = omit,
        overage_pricing_bands: Iterable[PricingBand] | Omit = omit,
        plan_id: str | Omit = omit,
        plan_template_id: str | Omit = omit,
        segment: Dict[str, str] | Omit = omit,
        tiers_span_plan: bool | Omit = omit,
        type: Literal["DEBIT", "PRODUCT_CREDIT", "GLOBAL_CREDIT"] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PricingResponse:
        """
        Update Pricing for the given UUID.

        **Note:** Either `planId` or `planTemplateId` request parameters are required
        for this call to be valid. If you omit both, then you will receive a validation
        error.

        Args:
          pricing_bands

          start_date: The start date _(in ISO-8601 format)_ for when the Pricing starts to be active
              for the Plan of Plan Template._(Required)_

          accounting_product_id: Optional Product ID this Pricing should be attributed to for accounting purposes

          aggregation_id: UUID of the Aggregation used to create the Pricing. Use this when creating a
              Pricing for a segmented aggregation.

          code: Unique short code for the Pricing.

          compound_aggregation_id: UUID of the Compound Aggregation used to create the Pricing.

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

          minimum_spend: The minimum spend amount per billing cycle for end customer Accounts on a Plan
              to which the Pricing is applied.

          minimum_spend_bill_in_advance: The default value is **FALSE**.

              - When TRUE, minimum spend is billed at the start of each billing period.

              - When FALSE, minimum spend is billed at the end of each billing period.

              _(Optional)_. Overrides the setting at Organization level for minimum spend
              billing in arrears/in advance.

          minimum_spend_description: Minimum spend description _(displayed on the bill line item)_.

          overage_pricing_bands: Specify Prepayment/Balance overage pricing in pricing bands for the case of a
              **Tiered** pricing structure.

          plan_id: UUID of the Plan the Pricing is created for.

          plan_template_id: UUID of the Plan Template the Pricing is created for.

          segment: Specifies the segment value which you are defining a Pricing for using this
              call:

              - For each segment value defined on a Segmented Aggregation you must create a
                separate Pricing and use the appropriate `aggregationId` parameter for the
                call.
              - If you specify a segment value that has not been defined for the Aggregation,
                you'll receive an error.
              - If you've defined segment values for the Aggregation using a single wildcard
                or multiple wildcards, you can create Pricing for these wildcard segment
                values also.

              For more details on creating Pricings for segment values on a Segmented
              Aggregation using this call, together with some examples, see the
              [Using API Call to Create Segmented Pricings](https://www.m3ter.com/docs/guides/plans-and-pricing/pricing-plans/pricing-plans-using-segmented-aggregations#using-api-call-to-create-a-segmented-pricing)
              in our User Documentation.

          tiers_span_plan: The default value is **FALSE**.

              - If TRUE, usage accumulates over the entire period the priced Plan is active
                for the account, and is not reset for pricing band rates at the start of each
                billing period.

              - If FALSE, usage does not accumulate, and is reset for pricing bands at the
                start of each billing period.

          type: - **DEBIT**. Default setting. The amount calculated using the Pricing is added
                to the bill as a debit.

              - **PRODUCT_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the same Product.

              - **GLOBAL_CREDIT**. The amount calculated using the Pricing is added to the
                bill as a credit _(negative amount)_. To prevent negative billing, the bill
                will be capped at the total of other line items for the entire bill, which
                might include other Products the Account consumes.

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
            f"/organizations/{org_id}/pricings/{id}",
            body=await async_maybe_transform(
                {
                    "pricing_bands": pricing_bands,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "aggregation_id": aggregation_id,
                    "code": code,
                    "compound_aggregation_id": compound_aggregation_id,
                    "cumulative": cumulative,
                    "description": description,
                    "end_date": end_date,
                    "minimum_spend": minimum_spend,
                    "minimum_spend_bill_in_advance": minimum_spend_bill_in_advance,
                    "minimum_spend_description": minimum_spend_description,
                    "overage_pricing_bands": overage_pricing_bands,
                    "plan_id": plan_id,
                    "plan_template_id": plan_template_id,
                    "segment": segment,
                    "tiers_span_plan": tiers_span_plan,
                    "type": type,
                    "version": version,
                },
                pricing_update_params.PricingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        aggregation_id: str | Omit = omit,
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
    ) -> AsyncPaginator[PricingResponse, AsyncCursor[PricingResponse]]:
        """
        Retrieve a list of Pricings filtered by date, Plan ID, PlanTemplate ID, or
        Pricing ID.

        Args:
          aggregation_id: UUID of the Aggregation to retrieve pricings for

          date: Date on which to retrieve active Pricings.

          ids: List of Pricing IDs to retrieve.

          next_token: `nextToken` for multi-page retrievals.

          page_size: Number of Pricings to retrieve per page.

          plan_id: UUID of the Plan to retrieve Pricings for.

          plan_template_id: UUID of the PlanTemplate to retrieve Pricings for.

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
            f"/organizations/{org_id}/pricings",
            page=AsyncCursor[PricingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "aggregation_id": aggregation_id,
                        "date": date,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "plan_id": plan_id,
                        "plan_template_id": plan_template_id,
                    },
                    pricing_list_params.PricingListParams,
                ),
            ),
            model=PricingResponse,
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
    ) -> PricingResponse:
        """
        Delete the Pricing with the given UUID.

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
            f"/organizations/{org_id}/pricings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PricingResponse,
        )


class PricingsResourceWithRawResponse:
    def __init__(self, pricings: PricingsResource) -> None:
        self._pricings = pricings

        self.create = to_raw_response_wrapper(
            pricings.create,
        )
        self.retrieve = to_raw_response_wrapper(
            pricings.retrieve,
        )
        self.update = to_raw_response_wrapper(
            pricings.update,
        )
        self.list = to_raw_response_wrapper(
            pricings.list,
        )
        self.delete = to_raw_response_wrapper(
            pricings.delete,
        )


class AsyncPricingsResourceWithRawResponse:
    def __init__(self, pricings: AsyncPricingsResource) -> None:
        self._pricings = pricings

        self.create = async_to_raw_response_wrapper(
            pricings.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            pricings.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            pricings.update,
        )
        self.list = async_to_raw_response_wrapper(
            pricings.list,
        )
        self.delete = async_to_raw_response_wrapper(
            pricings.delete,
        )


class PricingsResourceWithStreamingResponse:
    def __init__(self, pricings: PricingsResource) -> None:
        self._pricings = pricings

        self.create = to_streamed_response_wrapper(
            pricings.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            pricings.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            pricings.update,
        )
        self.list = to_streamed_response_wrapper(
            pricings.list,
        )
        self.delete = to_streamed_response_wrapper(
            pricings.delete,
        )


class AsyncPricingsResourceWithStreamingResponse:
    def __init__(self, pricings: AsyncPricingsResource) -> None:
        self._pricings = pricings

        self.create = async_to_streamed_response_wrapper(
            pricings.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            pricings.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            pricings.update,
        )
        self.list = async_to_streamed_response_wrapper(
            pricings.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            pricings.delete,
        )
