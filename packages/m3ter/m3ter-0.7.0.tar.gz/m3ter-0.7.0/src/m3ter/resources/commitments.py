# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from datetime import date
from typing_extensions import Literal

import httpx

from ..types import commitment_list_params, commitment_create_params, commitment_search_params, commitment_update_params
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
from ..types.commitment_response import CommitmentResponse
from ..types.commitment_fee_param import CommitmentFeeParam
from ..types.commitment_search_response import CommitmentSearchResponse

__all__ = ["CommitmentsResource", "AsyncCommitmentsResource"]


class CommitmentsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CommitmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CommitmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CommitmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CommitmentsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        amount: float,
        currency: str,
        end_date: Union[str, date],
        start_date: Union[str, date],
        accounting_product_id: str | Omit = omit,
        amount_first_bill: float | Omit = omit,
        amount_pre_paid: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        billing_interval: int | Omit = omit,
        billing_offset: int | Omit = omit,
        billing_plan_id: str | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        commitment_fee_description: str | Omit = omit,
        commitment_usage_description: str | Omit = omit,
        contract_id: str | Omit = omit,
        drawdowns_accounting_product_id: str | Omit = omit,
        fee_dates: Iterable[CommitmentFeeParam] | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ]
        | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        separate_overage_usage: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentResponse:
        """Create a new Commitment.

        Creates a new Commitment for an Organization.

        The request body must include all
        the necessary details such as the agreed amount, overage surcharge percentage,
        and the associated account and product details.

        **Note:** If some of the agreed Commitment amount remains unpaid at the start of
        an end-customer contract period, when you create a Commitment for an Account you
        can set up billing for the outstanding amount in one of two ways:

        - Select a Product _Plan to bill with_. Use the `billingPlanId` request
          parameter to select the Plan used for billing.
        - Define a _schedule of billing dates_. Omit a `billingPlanId` and use the
          `feeDates` request parameter to define a precise schedule of bill dates and
          amounts.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account the Commitment is
              added to.

          amount: The total amount that the customer has committed to pay.

          currency: The currency used for the Commitment. For example: USD.

          end_date: The end date of the Commitment period in ISO-8601 format.

              **Note:** End date is exclusive - if you set an end date of June 1st 2022, then
              the Commitment ceases to be active for the Account at midnight on May 31st 2022,
              and any Prepayment fees due are calculated up to that point in time, NOT up to
              midnight on June 1st

          start_date: The start date of the Commitment period in ISO-8601 format.

          accounting_product_id: The unique identifier (UUID) for the Product linked to the Commitment for
              accounting purposes. _(Optional)_

              **NOTE:** If you're planning to set up an integration for sending Bills to an
              external accounts receivable system, please check requirements for your chosen
              system. Some systems, such as NetSuite, require a Product to be linked with any
              Bill line items associated with Account Commitments, and the integration will
              fail if this is not present

          amount_first_bill: The amount to be billed in the first invoice.

          amount_pre_paid: The amount that the customer has already paid upfront at the start of the
              Commitment service period.

          bill_epoch: The starting date _(in ISO-8601 date format)_ from which the billing cycles are
              calculated.

          billing_interval: How often the Commitment fees are applied to bills. For example, if the plan
              being used to bill for Commitment fees is set to issue bills every three months
              and the `billingInterval` is set to 2, then the Commitment fees are applied
              every six months.

          billing_offset: Defines an offset for when the Commitment fees are first applied to bills on the
              Account. For example, if bills are issued every three months and the
              `billingOffset` is 0, then the charge is applied to the first bill (at three
              months); if set to 1, it's applied to the next bill (at six months), and so on.

          billing_plan_id: The unique identifier (UUID) for the Product Plan used for billing Commitment
              fees due.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          commitment_fee_bill_in_advance: A boolean value indicating whether the Commitment fee is billed in advance
              _(start of each billing period)_ or arrears _(end of each billing period)_.

              If no value is supplied, then the Organization Configuration value is used.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          commitment_fee_description: A textual description of the Commitment fee.

          commitment_usage_description: A textual description of the Commitment usage.

          contract_id: The unique identifier (UUID) for a Contract you've created for the Account -
              used to add the Commitment to this Contract.

              **Note:** If you associate the Commitment with a Contract you must ensure the
              Account Plan attached to the Account has the same Contract associated with it.
              If the Account Plan Contract and Commitment Contract do not match, then at
              billing the Commitment amount will not be drawn-down against.

          drawdowns_accounting_product_id: Optional Product ID this Commitment consumptions should be attributed to for
              accounting purposes

          fee_dates: Used for billing any outstanding Commitment fees _on a schedule_.

              Create an array to define a series of bill dates and amounts covering specified
              service periods:

              - `date` - the billing date _(in ISO-8601 format)_.
              - `amount` - the billed amount.
              - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
                period the bill covers _(in ISO-8601 format)_.

              **Notes:**

              - If you try to set `servicePeriodStartDate` _after_ `servicePeriodEndDate`,
                you'll receive an error.
              - You can set `servicePeriodStartDate` and `servicePeriodEndDate` to the _same
                date_ without receiving an error, but _please be sure_ your Commitment billing
                use case requires this.

          fees_accounting_product_id: Optional Product ID this Commitment fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Commitment amount. Options are:

              - `MINIMUM_SPEND`
              - `STANDING_CHARGE`
              - `USAGE`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Commitment amount at billing.

          overage_description: A textual description of the overage charges.

          overage_surcharge_percent: The percentage surcharge applied to usage charges that exceed the Commitment
              amount.

              **Note:** You can enter a _negative percentage_ if you want to give a discount
              rate for usage to end customers who exceed their Commitment amount

          product_ids: A list of unique identifiers (UUIDs) for Products the Account consumes. Charges
              due for these Products will be made available for draw-down against the
              Commitment.

              **Note:** If not used, then charges due for all Products the Account consumes
              will be made available for draw-down against the Commitment.

          separate_overage_usage: A boolean value indicating whether the overage usage is billed separately or
              together. If overage usage is separated and a Commitment amount has been
              consumed by an Account, any subsequent line items on Bills against the Account
              for usage will show as separate "overage usage" charges, not simply as "usage"
              charges:

              - **TRUE** - billed separately.
              - **FALSE** - billed together.

              **Notes:**

              - Can be used only if no value or 0 has been defined for the
                `overageSurchargePercent` parameter. If you try to separate overage usage when
                a value other than 0 has been defined for `overageSurchargePercent`, you'll
                receive an error.
              - If a priced Plan is used to bill any outstanding Commitment fees due and the
                Plan is set up with overage pricing on a _tiered pricing structure_ and you
                enable separate bill line items for overage usage, then overage usage charges
                will be rated according to the overage pricing defined for the tiered pricing
                on the Plan.

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
            f"/organizations/{org_id}/commitments",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "amount": amount,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount_first_bill": amount_first_bill,
                    "amount_pre_paid": amount_pre_paid,
                    "bill_epoch": bill_epoch,
                    "billing_interval": billing_interval,
                    "billing_offset": billing_offset,
                    "billing_plan_id": billing_plan_id,
                    "child_billing_mode": child_billing_mode,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "commitment_fee_description": commitment_fee_description,
                    "commitment_usage_description": commitment_usage_description,
                    "contract_id": contract_id,
                    "drawdowns_accounting_product_id": drawdowns_accounting_product_id,
                    "fee_dates": fee_dates,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "separate_overage_usage": separate_overage_usage,
                    "version": version,
                },
                commitment_create_params.CommitmentCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
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
    ) -> CommitmentResponse:
        """
        Retrieve a specific Commitment.

        Retrieve the details of the Commitment with the given UUID. It provides
        comprehensive information about the Commitment, such as the agreed amount,
        overage surcharge percentage, and other related details.

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
            f"/organizations/{org_id}/commitments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        amount: float,
        currency: str,
        end_date: Union[str, date],
        start_date: Union[str, date],
        accounting_product_id: str | Omit = omit,
        amount_first_bill: float | Omit = omit,
        amount_pre_paid: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        billing_interval: int | Omit = omit,
        billing_offset: int | Omit = omit,
        billing_plan_id: str | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        commitment_fee_description: str | Omit = omit,
        commitment_usage_description: str | Omit = omit,
        contract_id: str | Omit = omit,
        drawdowns_accounting_product_id: str | Omit = omit,
        fee_dates: Iterable[CommitmentFeeParam] | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ]
        | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        separate_overage_usage: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentResponse:
        """
        Modify a specific Commitment.

        Update the details of the Commitment with the given UUID. Use this endpoint to
        adjust Commitment parameters such as the fixed amount, overage surcharge
        percentage, or associated contract details.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account the Commitment is
              added to.

          amount: The total amount that the customer has committed to pay.

          currency: The currency used for the Commitment. For example: USD.

          end_date: The end date of the Commitment period in ISO-8601 format.

              **Note:** End date is exclusive - if you set an end date of June 1st 2022, then
              the Commitment ceases to be active for the Account at midnight on May 31st 2022,
              and any Prepayment fees due are calculated up to that point in time, NOT up to
              midnight on June 1st

          start_date: The start date of the Commitment period in ISO-8601 format.

          accounting_product_id: The unique identifier (UUID) for the Product linked to the Commitment for
              accounting purposes. _(Optional)_

              **NOTE:** If you're planning to set up an integration for sending Bills to an
              external accounts receivable system, please check requirements for your chosen
              system. Some systems, such as NetSuite, require a Product to be linked with any
              Bill line items associated with Account Commitments, and the integration will
              fail if this is not present

          amount_first_bill: The amount to be billed in the first invoice.

          amount_pre_paid: The amount that the customer has already paid upfront at the start of the
              Commitment service period.

          bill_epoch: The starting date _(in ISO-8601 date format)_ from which the billing cycles are
              calculated.

          billing_interval: How often the Commitment fees are applied to bills. For example, if the plan
              being used to bill for Commitment fees is set to issue bills every three months
              and the `billingInterval` is set to 2, then the Commitment fees are applied
              every six months.

          billing_offset: Defines an offset for when the Commitment fees are first applied to bills on the
              Account. For example, if bills are issued every three months and the
              `billingOffset` is 0, then the charge is applied to the first bill (at three
              months); if set to 1, it's applied to the next bill (at six months), and so on.

          billing_plan_id: The unique identifier (UUID) for the Product Plan used for billing Commitment
              fees due.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          commitment_fee_bill_in_advance: A boolean value indicating whether the Commitment fee is billed in advance
              _(start of each billing period)_ or arrears _(end of each billing period)_.

              If no value is supplied, then the Organization Configuration value is used.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          commitment_fee_description: A textual description of the Commitment fee.

          commitment_usage_description: A textual description of the Commitment usage.

          contract_id: The unique identifier (UUID) for a Contract you've created for the Account -
              used to add the Commitment to this Contract.

              **Note:** If you associate the Commitment with a Contract you must ensure the
              Account Plan attached to the Account has the same Contract associated with it.
              If the Account Plan Contract and Commitment Contract do not match, then at
              billing the Commitment amount will not be drawn-down against.

          drawdowns_accounting_product_id: Optional Product ID this Commitment consumptions should be attributed to for
              accounting purposes

          fee_dates: Used for billing any outstanding Commitment fees _on a schedule_.

              Create an array to define a series of bill dates and amounts covering specified
              service periods:

              - `date` - the billing date _(in ISO-8601 format)_.
              - `amount` - the billed amount.
              - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
                period the bill covers _(in ISO-8601 format)_.

              **Notes:**

              - If you try to set `servicePeriodStartDate` _after_ `servicePeriodEndDate`,
                you'll receive an error.
              - You can set `servicePeriodStartDate` and `servicePeriodEndDate` to the _same
                date_ without receiving an error, but _please be sure_ your Commitment billing
                use case requires this.

          fees_accounting_product_id: Optional Product ID this Commitment fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Commitment amount. Options are:

              - `MINIMUM_SPEND`
              - `STANDING_CHARGE`
              - `USAGE`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Commitment amount at billing.

          overage_description: A textual description of the overage charges.

          overage_surcharge_percent: The percentage surcharge applied to usage charges that exceed the Commitment
              amount.

              **Note:** You can enter a _negative percentage_ if you want to give a discount
              rate for usage to end customers who exceed their Commitment amount

          product_ids: A list of unique identifiers (UUIDs) for Products the Account consumes. Charges
              due for these Products will be made available for draw-down against the
              Commitment.

              **Note:** If not used, then charges due for all Products the Account consumes
              will be made available for draw-down against the Commitment.

          separate_overage_usage: A boolean value indicating whether the overage usage is billed separately or
              together. If overage usage is separated and a Commitment amount has been
              consumed by an Account, any subsequent line items on Bills against the Account
              for usage will show as separate "overage usage" charges, not simply as "usage"
              charges:

              - **TRUE** - billed separately.
              - **FALSE** - billed together.

              **Notes:**

              - Can be used only if no value or 0 has been defined for the
                `overageSurchargePercent` parameter. If you try to separate overage usage when
                a value other than 0 has been defined for `overageSurchargePercent`, you'll
                receive an error.
              - If a priced Plan is used to bill any outstanding Commitment fees due and the
                Plan is set up with overage pricing on a _tiered pricing structure_ and you
                enable separate bill line items for overage usage, then overage usage charges
                will be rated according to the overage pricing defined for the tiered pricing
                on the Plan.

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
            f"/organizations/{org_id}/commitments/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "amount": amount,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount_first_bill": amount_first_bill,
                    "amount_pre_paid": amount_pre_paid,
                    "bill_epoch": bill_epoch,
                    "billing_interval": billing_interval,
                    "billing_offset": billing_offset,
                    "billing_plan_id": billing_plan_id,
                    "child_billing_mode": child_billing_mode,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "commitment_fee_description": commitment_fee_description,
                    "commitment_usage_description": commitment_usage_description,
                    "contract_id": contract_id,
                    "drawdowns_accounting_product_id": drawdowns_accounting_product_id,
                    "fee_dates": fee_dates,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "separate_overage_usage": separate_overage_usage,
                    "version": version,
                },
                commitment_update_params.CommitmentUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        contract_id: Optional[str] | Omit = omit,
        date: str | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
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
    ) -> SyncCursor[CommitmentResponse]:
        """
        Retrieve a list of Commitments.

        Retrieves a list of all Commitments associated with an Organization. This
        endpoint supports pagination and includes various query parameters to filter the
        Commitments based on Account, Product, date, and end dates.

        Args:
          account_id: The unique identifier (UUID) for the Account. This parameter helps filter the
              Commitments related to a specific end-customer Account.

          date: A date _(in ISO-8601 format)_ to filter Commitments which are active on this
              specific date.

          end_date_end: A date _(in ISO-8601 format)_ used to filter Commitments. Only Commitments with
              end dates before this date will be included.

          end_date_start: A date _(in ISO-8601 format)_ used to filter Commitments. Only Commitments with
              end dates on or after this date will be included.

          ids: A list of unique identifiers (UUIDs) for the Commitments to retrieve. Use this
              to fetch specific Commitments in a single request.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Commitments in a paginated list.

          page_size: Specifies the maximum number of Commitments to retrieve per page.

          product_id: The unique identifier (UUID) for the Product. This parameter helps filter the
              Commitments related to a specific Product.

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
            f"/organizations/{org_id}/commitments",
            page=SyncCursor[CommitmentResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "contract_id": contract_id,
                        "date": date,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    commitment_list_params.CommitmentListParams,
                ),
            ),
            model=CommitmentResponse,
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
    ) -> CommitmentResponse:
        """Remove a specific Commitment.

        Deletes the Commitment with the given UUID.

        Use this endpoint when a Commitment
        is no longer valid or needs to be removed from the system.

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
            f"/organizations/{org_id}/commitments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    def search(
        self,
        *,
        org_id: str | None = None,
        from_document: int | Omit = omit,
        operator: Literal["AND", "OR"] | Omit = omit,
        page_size: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["ASC", "DESC"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentSearchResponse:
        """
        Search for commitment entities.

        This endpoint executes a search query for Commitments based on the user
        specified search criteria. The search query is customizable, allowing for
        complex nested conditions and sorting. The returned list of Commitments can be
        paginated for easier management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Commitments to retrieve per page.

              **NOTE:** If not defined, default is 10.

          search_query:
              Query for data using special syntax:

              - Query parameters should be delimited using $ (dollar sign).
              - Allowed comparators are:
                - (greater than) >
                - (greater than or equal to) >=
                - (equal to) :
                - (less than) <
                - (less than or equal to) <=
                - (match phrase/prefix) ~
              - Allowed parameters: startDate, endDate, contractId, accountId, productId,
                productIds, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=startDate>2023-01-01$accountId:062085ab-a301-4f21-a081-411020864452.
                - This query is translated into: find commitments where the startDate is older
                  than 2023-01-01 AND the accountId is equal to
                  062085ab-a301-4f21-a081-411020864452.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Commitment entity to sort by, such as `accountId`, `endDate`, and so on.

          sort_order: Sorting order.

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
            f"/organizations/{org_id}/commitments/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "from_document": from_document,
                        "operator": operator,
                        "page_size": page_size,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                    },
                    commitment_search_params.CommitmentSearchParams,
                ),
            ),
            cast_to=CommitmentSearchResponse,
        )


class AsyncCommitmentsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCommitmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCommitmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCommitmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCommitmentsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        amount: float,
        currency: str,
        end_date: Union[str, date],
        start_date: Union[str, date],
        accounting_product_id: str | Omit = omit,
        amount_first_bill: float | Omit = omit,
        amount_pre_paid: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        billing_interval: int | Omit = omit,
        billing_offset: int | Omit = omit,
        billing_plan_id: str | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        commitment_fee_description: str | Omit = omit,
        commitment_usage_description: str | Omit = omit,
        contract_id: str | Omit = omit,
        drawdowns_accounting_product_id: str | Omit = omit,
        fee_dates: Iterable[CommitmentFeeParam] | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ]
        | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        separate_overage_usage: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentResponse:
        """Create a new Commitment.

        Creates a new Commitment for an Organization.

        The request body must include all
        the necessary details such as the agreed amount, overage surcharge percentage,
        and the associated account and product details.

        **Note:** If some of the agreed Commitment amount remains unpaid at the start of
        an end-customer contract period, when you create a Commitment for an Account you
        can set up billing for the outstanding amount in one of two ways:

        - Select a Product _Plan to bill with_. Use the `billingPlanId` request
          parameter to select the Plan used for billing.
        - Define a _schedule of billing dates_. Omit a `billingPlanId` and use the
          `feeDates` request parameter to define a precise schedule of bill dates and
          amounts.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account the Commitment is
              added to.

          amount: The total amount that the customer has committed to pay.

          currency: The currency used for the Commitment. For example: USD.

          end_date: The end date of the Commitment period in ISO-8601 format.

              **Note:** End date is exclusive - if you set an end date of June 1st 2022, then
              the Commitment ceases to be active for the Account at midnight on May 31st 2022,
              and any Prepayment fees due are calculated up to that point in time, NOT up to
              midnight on June 1st

          start_date: The start date of the Commitment period in ISO-8601 format.

          accounting_product_id: The unique identifier (UUID) for the Product linked to the Commitment for
              accounting purposes. _(Optional)_

              **NOTE:** If you're planning to set up an integration for sending Bills to an
              external accounts receivable system, please check requirements for your chosen
              system. Some systems, such as NetSuite, require a Product to be linked with any
              Bill line items associated with Account Commitments, and the integration will
              fail if this is not present

          amount_first_bill: The amount to be billed in the first invoice.

          amount_pre_paid: The amount that the customer has already paid upfront at the start of the
              Commitment service period.

          bill_epoch: The starting date _(in ISO-8601 date format)_ from which the billing cycles are
              calculated.

          billing_interval: How often the Commitment fees are applied to bills. For example, if the plan
              being used to bill for Commitment fees is set to issue bills every three months
              and the `billingInterval` is set to 2, then the Commitment fees are applied
              every six months.

          billing_offset: Defines an offset for when the Commitment fees are first applied to bills on the
              Account. For example, if bills are issued every three months and the
              `billingOffset` is 0, then the charge is applied to the first bill (at three
              months); if set to 1, it's applied to the next bill (at six months), and so on.

          billing_plan_id: The unique identifier (UUID) for the Product Plan used for billing Commitment
              fees due.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          commitment_fee_bill_in_advance: A boolean value indicating whether the Commitment fee is billed in advance
              _(start of each billing period)_ or arrears _(end of each billing period)_.

              If no value is supplied, then the Organization Configuration value is used.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          commitment_fee_description: A textual description of the Commitment fee.

          commitment_usage_description: A textual description of the Commitment usage.

          contract_id: The unique identifier (UUID) for a Contract you've created for the Account -
              used to add the Commitment to this Contract.

              **Note:** If you associate the Commitment with a Contract you must ensure the
              Account Plan attached to the Account has the same Contract associated with it.
              If the Account Plan Contract and Commitment Contract do not match, then at
              billing the Commitment amount will not be drawn-down against.

          drawdowns_accounting_product_id: Optional Product ID this Commitment consumptions should be attributed to for
              accounting purposes

          fee_dates: Used for billing any outstanding Commitment fees _on a schedule_.

              Create an array to define a series of bill dates and amounts covering specified
              service periods:

              - `date` - the billing date _(in ISO-8601 format)_.
              - `amount` - the billed amount.
              - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
                period the bill covers _(in ISO-8601 format)_.

              **Notes:**

              - If you try to set `servicePeriodStartDate` _after_ `servicePeriodEndDate`,
                you'll receive an error.
              - You can set `servicePeriodStartDate` and `servicePeriodEndDate` to the _same
                date_ without receiving an error, but _please be sure_ your Commitment billing
                use case requires this.

          fees_accounting_product_id: Optional Product ID this Commitment fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Commitment amount. Options are:

              - `MINIMUM_SPEND`
              - `STANDING_CHARGE`
              - `USAGE`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Commitment amount at billing.

          overage_description: A textual description of the overage charges.

          overage_surcharge_percent: The percentage surcharge applied to usage charges that exceed the Commitment
              amount.

              **Note:** You can enter a _negative percentage_ if you want to give a discount
              rate for usage to end customers who exceed their Commitment amount

          product_ids: A list of unique identifiers (UUIDs) for Products the Account consumes. Charges
              due for these Products will be made available for draw-down against the
              Commitment.

              **Note:** If not used, then charges due for all Products the Account consumes
              will be made available for draw-down against the Commitment.

          separate_overage_usage: A boolean value indicating whether the overage usage is billed separately or
              together. If overage usage is separated and a Commitment amount has been
              consumed by an Account, any subsequent line items on Bills against the Account
              for usage will show as separate "overage usage" charges, not simply as "usage"
              charges:

              - **TRUE** - billed separately.
              - **FALSE** - billed together.

              **Notes:**

              - Can be used only if no value or 0 has been defined for the
                `overageSurchargePercent` parameter. If you try to separate overage usage when
                a value other than 0 has been defined for `overageSurchargePercent`, you'll
                receive an error.
              - If a priced Plan is used to bill any outstanding Commitment fees due and the
                Plan is set up with overage pricing on a _tiered pricing structure_ and you
                enable separate bill line items for overage usage, then overage usage charges
                will be rated according to the overage pricing defined for the tiered pricing
                on the Plan.

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
            f"/organizations/{org_id}/commitments",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "amount": amount,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount_first_bill": amount_first_bill,
                    "amount_pre_paid": amount_pre_paid,
                    "bill_epoch": bill_epoch,
                    "billing_interval": billing_interval,
                    "billing_offset": billing_offset,
                    "billing_plan_id": billing_plan_id,
                    "child_billing_mode": child_billing_mode,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "commitment_fee_description": commitment_fee_description,
                    "commitment_usage_description": commitment_usage_description,
                    "contract_id": contract_id,
                    "drawdowns_accounting_product_id": drawdowns_accounting_product_id,
                    "fee_dates": fee_dates,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "separate_overage_usage": separate_overage_usage,
                    "version": version,
                },
                commitment_create_params.CommitmentCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
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
    ) -> CommitmentResponse:
        """
        Retrieve a specific Commitment.

        Retrieve the details of the Commitment with the given UUID. It provides
        comprehensive information about the Commitment, such as the agreed amount,
        overage surcharge percentage, and other related details.

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
            f"/organizations/{org_id}/commitments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        amount: float,
        currency: str,
        end_date: Union[str, date],
        start_date: Union[str, date],
        accounting_product_id: str | Omit = omit,
        amount_first_bill: float | Omit = omit,
        amount_pre_paid: float | Omit = omit,
        bill_epoch: Union[str, date] | Omit = omit,
        billing_interval: int | Omit = omit,
        billing_offset: int | Omit = omit,
        billing_plan_id: str | Omit = omit,
        child_billing_mode: Literal["PARENT_SUMMARY", "PARENT_BREAKDOWN", "CHILD"] | Omit = omit,
        commitment_fee_bill_in_advance: bool | Omit = omit,
        commitment_fee_description: str | Omit = omit,
        commitment_usage_description: str | Omit = omit,
        contract_id: str | Omit = omit,
        drawdowns_accounting_product_id: str | Omit = omit,
        fee_dates: Iterable[CommitmentFeeParam] | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE", "USAGE", "MINIMUM_SPEND", "COUNTER_RUNNING_TOTAL_CHARGE", "COUNTER_ADJUSTMENT_DEBIT"
            ]
        ]
        | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        separate_overage_usage: bool | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentResponse:
        """
        Modify a specific Commitment.

        Update the details of the Commitment with the given UUID. Use this endpoint to
        adjust Commitment parameters such as the fixed amount, overage surcharge
        percentage, or associated contract details.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account the Commitment is
              added to.

          amount: The total amount that the customer has committed to pay.

          currency: The currency used for the Commitment. For example: USD.

          end_date: The end date of the Commitment period in ISO-8601 format.

              **Note:** End date is exclusive - if you set an end date of June 1st 2022, then
              the Commitment ceases to be active for the Account at midnight on May 31st 2022,
              and any Prepayment fees due are calculated up to that point in time, NOT up to
              midnight on June 1st

          start_date: The start date of the Commitment period in ISO-8601 format.

          accounting_product_id: The unique identifier (UUID) for the Product linked to the Commitment for
              accounting purposes. _(Optional)_

              **NOTE:** If you're planning to set up an integration for sending Bills to an
              external accounts receivable system, please check requirements for your chosen
              system. Some systems, such as NetSuite, require a Product to be linked with any
              Bill line items associated with Account Commitments, and the integration will
              fail if this is not present

          amount_first_bill: The amount to be billed in the first invoice.

          amount_pre_paid: The amount that the customer has already paid upfront at the start of the
              Commitment service period.

          bill_epoch: The starting date _(in ISO-8601 date format)_ from which the billing cycles are
              calculated.

          billing_interval: How often the Commitment fees are applied to bills. For example, if the plan
              being used to bill for Commitment fees is set to issue bills every three months
              and the `billingInterval` is set to 2, then the Commitment fees are applied
              every six months.

          billing_offset: Defines an offset for when the Commitment fees are first applied to bills on the
              Account. For example, if bills are issued every three months and the
              `billingOffset` is 0, then the charge is applied to the first bill (at three
              months); if set to 1, it's applied to the next bill (at six months), and so on.

          billing_plan_id: The unique identifier (UUID) for the Product Plan used for billing Commitment
              fees due.

          child_billing_mode: If the Account is either a Parent or a Child Account, this specifies the Account
              hierarchy billing mode. The mode determines how billing will be handled and
              shown on bills for charges due on the Parent Account, and charges due on Child
              Accounts:

              - **Parent Breakdown** - a separate bill line item per Account. Default setting.

              - **Parent Summary** - single bill line item for all Accounts.

              - **Child** - the Child Account is billed.

          commitment_fee_bill_in_advance: A boolean value indicating whether the Commitment fee is billed in advance
              _(start of each billing period)_ or arrears _(end of each billing period)_.

              If no value is supplied, then the Organization Configuration value is used.

              - **TRUE** - bill in advance _(start of each billing period)_.
              - **FALSE** - bill in arrears _(end of each billing period)_.

          commitment_fee_description: A textual description of the Commitment fee.

          commitment_usage_description: A textual description of the Commitment usage.

          contract_id: The unique identifier (UUID) for a Contract you've created for the Account -
              used to add the Commitment to this Contract.

              **Note:** If you associate the Commitment with a Contract you must ensure the
              Account Plan attached to the Account has the same Contract associated with it.
              If the Account Plan Contract and Commitment Contract do not match, then at
              billing the Commitment amount will not be drawn-down against.

          drawdowns_accounting_product_id: Optional Product ID this Commitment consumptions should be attributed to for
              accounting purposes

          fee_dates: Used for billing any outstanding Commitment fees _on a schedule_.

              Create an array to define a series of bill dates and amounts covering specified
              service periods:

              - `date` - the billing date _(in ISO-8601 format)_.
              - `amount` - the billed amount.
              - `servicePeriodStartDate` and `servicePeriodEndDate` - defines the service
                period the bill covers _(in ISO-8601 format)_.

              **Notes:**

              - If you try to set `servicePeriodStartDate` _after_ `servicePeriodEndDate`,
                you'll receive an error.
              - You can set `servicePeriodStartDate` and `servicePeriodEndDate` to the _same
                date_ without receiving an error, but _please be sure_ your Commitment billing
                use case requires this.

          fees_accounting_product_id: Optional Product ID this Commitment fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Commitment amount. Options are:

              - `MINIMUM_SPEND`
              - `STANDING_CHARGE`
              - `USAGE`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Commitment amount at billing.

          overage_description: A textual description of the overage charges.

          overage_surcharge_percent: The percentage surcharge applied to usage charges that exceed the Commitment
              amount.

              **Note:** You can enter a _negative percentage_ if you want to give a discount
              rate for usage to end customers who exceed their Commitment amount

          product_ids: A list of unique identifiers (UUIDs) for Products the Account consumes. Charges
              due for these Products will be made available for draw-down against the
              Commitment.

              **Note:** If not used, then charges due for all Products the Account consumes
              will be made available for draw-down against the Commitment.

          separate_overage_usage: A boolean value indicating whether the overage usage is billed separately or
              together. If overage usage is separated and a Commitment amount has been
              consumed by an Account, any subsequent line items on Bills against the Account
              for usage will show as separate "overage usage" charges, not simply as "usage"
              charges:

              - **TRUE** - billed separately.
              - **FALSE** - billed together.

              **Notes:**

              - Can be used only if no value or 0 has been defined for the
                `overageSurchargePercent` parameter. If you try to separate overage usage when
                a value other than 0 has been defined for `overageSurchargePercent`, you'll
                receive an error.
              - If a priced Plan is used to bill any outstanding Commitment fees due and the
                Plan is set up with overage pricing on a _tiered pricing structure_ and you
                enable separate bill line items for overage usage, then overage usage charges
                will be rated according to the overage pricing defined for the tiered pricing
                on the Plan.

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
            f"/organizations/{org_id}/commitments/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "amount": amount,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "accounting_product_id": accounting_product_id,
                    "amount_first_bill": amount_first_bill,
                    "amount_pre_paid": amount_pre_paid,
                    "bill_epoch": bill_epoch,
                    "billing_interval": billing_interval,
                    "billing_offset": billing_offset,
                    "billing_plan_id": billing_plan_id,
                    "child_billing_mode": child_billing_mode,
                    "commitment_fee_bill_in_advance": commitment_fee_bill_in_advance,
                    "commitment_fee_description": commitment_fee_description,
                    "commitment_usage_description": commitment_usage_description,
                    "contract_id": contract_id,
                    "drawdowns_accounting_product_id": drawdowns_accounting_product_id,
                    "fee_dates": fee_dates,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "separate_overage_usage": separate_overage_usage,
                    "version": version,
                },
                commitment_update_params.CommitmentUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        contract_id: Optional[str] | Omit = omit,
        date: str | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
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
    ) -> AsyncPaginator[CommitmentResponse, AsyncCursor[CommitmentResponse]]:
        """
        Retrieve a list of Commitments.

        Retrieves a list of all Commitments associated with an Organization. This
        endpoint supports pagination and includes various query parameters to filter the
        Commitments based on Account, Product, date, and end dates.

        Args:
          account_id: The unique identifier (UUID) for the Account. This parameter helps filter the
              Commitments related to a specific end-customer Account.

          date: A date _(in ISO-8601 format)_ to filter Commitments which are active on this
              specific date.

          end_date_end: A date _(in ISO-8601 format)_ used to filter Commitments. Only Commitments with
              end dates before this date will be included.

          end_date_start: A date _(in ISO-8601 format)_ used to filter Commitments. Only Commitments with
              end dates on or after this date will be included.

          ids: A list of unique identifiers (UUIDs) for the Commitments to retrieve. Use this
              to fetch specific Commitments in a single request.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Commitments in a paginated list.

          page_size: Specifies the maximum number of Commitments to retrieve per page.

          product_id: The unique identifier (UUID) for the Product. This parameter helps filter the
              Commitments related to a specific Product.

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
            f"/organizations/{org_id}/commitments",
            page=AsyncCursor[CommitmentResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "contract_id": contract_id,
                        "date": date,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                        "product_id": product_id,
                    },
                    commitment_list_params.CommitmentListParams,
                ),
            ),
            model=CommitmentResponse,
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
    ) -> CommitmentResponse:
        """Remove a specific Commitment.

        Deletes the Commitment with the given UUID.

        Use this endpoint when a Commitment
        is no longer valid or needs to be removed from the system.

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
            f"/organizations/{org_id}/commitments/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CommitmentResponse,
        )

    async def search(
        self,
        *,
        org_id: str | None = None,
        from_document: int | Omit = omit,
        operator: Literal["AND", "OR"] | Omit = omit,
        page_size: int | Omit = omit,
        search_query: str | Omit = omit,
        sort_by: str | Omit = omit,
        sort_order: Literal["ASC", "DESC"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CommitmentSearchResponse:
        """
        Search for commitment entities.

        This endpoint executes a search query for Commitments based on the user
        specified search criteria. The search query is customizable, allowing for
        complex nested conditions and sorting. The returned list of Commitments can be
        paginated for easier management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Commitments to retrieve per page.

              **NOTE:** If not defined, default is 10.

          search_query:
              Query for data using special syntax:

              - Query parameters should be delimited using $ (dollar sign).
              - Allowed comparators are:
                - (greater than) >
                - (greater than or equal to) >=
                - (equal to) :
                - (less than) <
                - (less than or equal to) <=
                - (match phrase/prefix) ~
              - Allowed parameters: startDate, endDate, contractId, accountId, productId,
                productIds, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=startDate>2023-01-01$accountId:062085ab-a301-4f21-a081-411020864452.
                - This query is translated into: find commitments where the startDate is older
                  than 2023-01-01 AND the accountId is equal to
                  062085ab-a301-4f21-a081-411020864452.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Commitment entity to sort by, such as `accountId`, `endDate`, and so on.

          sort_order: Sorting order.

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
            f"/organizations/{org_id}/commitments/search",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "from_document": from_document,
                        "operator": operator,
                        "page_size": page_size,
                        "search_query": search_query,
                        "sort_by": sort_by,
                        "sort_order": sort_order,
                    },
                    commitment_search_params.CommitmentSearchParams,
                ),
            ),
            cast_to=CommitmentSearchResponse,
        )


class CommitmentsResourceWithRawResponse:
    def __init__(self, commitments: CommitmentsResource) -> None:
        self._commitments = commitments

        self.create = to_raw_response_wrapper(
            commitments.create,
        )
        self.retrieve = to_raw_response_wrapper(
            commitments.retrieve,
        )
        self.update = to_raw_response_wrapper(
            commitments.update,
        )
        self.list = to_raw_response_wrapper(
            commitments.list,
        )
        self.delete = to_raw_response_wrapper(
            commitments.delete,
        )
        self.search = to_raw_response_wrapper(
            commitments.search,
        )


class AsyncCommitmentsResourceWithRawResponse:
    def __init__(self, commitments: AsyncCommitmentsResource) -> None:
        self._commitments = commitments

        self.create = async_to_raw_response_wrapper(
            commitments.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            commitments.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            commitments.update,
        )
        self.list = async_to_raw_response_wrapper(
            commitments.list,
        )
        self.delete = async_to_raw_response_wrapper(
            commitments.delete,
        )
        self.search = async_to_raw_response_wrapper(
            commitments.search,
        )


class CommitmentsResourceWithStreamingResponse:
    def __init__(self, commitments: CommitmentsResource) -> None:
        self._commitments = commitments

        self.create = to_streamed_response_wrapper(
            commitments.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            commitments.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            commitments.update,
        )
        self.list = to_streamed_response_wrapper(
            commitments.list,
        )
        self.delete = to_streamed_response_wrapper(
            commitments.delete,
        )
        self.search = to_streamed_response_wrapper(
            commitments.search,
        )


class AsyncCommitmentsResourceWithStreamingResponse:
    def __init__(self, commitments: AsyncCommitmentsResource) -> None:
        self._commitments = commitments

        self.create = async_to_streamed_response_wrapper(
            commitments.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            commitments.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            commitments.update,
        )
        self.list = async_to_streamed_response_wrapper(
            commitments.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            commitments.delete,
        )
        self.search = async_to_streamed_response_wrapper(
            commitments.search,
        )
