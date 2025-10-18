# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Optional
from datetime import datetime
from typing_extensions import Literal

import httpx

from ...types import balance_list_params, balance_create_params, balance_update_params
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursor, AsyncCursor
from .transactions import (
    TransactionsResource,
    AsyncTransactionsResource,
    TransactionsResourceWithRawResponse,
    AsyncTransactionsResourceWithRawResponse,
    TransactionsResourceWithStreamingResponse,
    AsyncTransactionsResourceWithStreamingResponse,
)
from ..._base_client import AsyncPaginator, make_request_options
from ...types.balance import Balance

__all__ = ["BalancesResource", "AsyncBalancesResource"]


class BalancesResource(SyncAPIResource):
    @cached_property
    def transactions(self) -> TransactionsResource:
        return TransactionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> BalancesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return BalancesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BalancesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return BalancesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        currency: str,
        end_date: Union[str, datetime],
        start_date: Union[str, datetime],
        balance_draw_down_description: str | Omit = omit,
        code: str | Omit = omit,
        consumptions_accounting_product_id: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ]
        | Omit = omit,
        name: str | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        rollover_amount: float | Omit = omit,
        rollover_end_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Balance:
        """
        Create a new Balance for the given end customer Account.

        This endpoint allows you to create a new Balance for a specific end customer
        Account. The Balance details should be provided in the request body.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account.

          currency: The currency code used for the Balance amount. For example: USD, GBP or EUR.

          end_date: The date _(in ISO 8601 format)_ after which the Balance will no longer be active
              for the Account.

              **Note:** You can use the `rolloverEndDate` request parameter to define an
              extended grace period for continued draw-down against the Balance if any amount
              remains when the specified `endDate` is reached.

          start_date: The date _(in ISO 8601 format)_ when the Balance becomes active.

          balance_draw_down_description: A description for the bill line items for draw-down charges against the Balance.
              _(Optional)._

          code: Unique short code for the Balance.

          consumptions_accounting_product_id: Optional Product ID this Balance Consumptions should be attributed to for
              accounting purposes

          contract_id

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: A description of the Balance.

          fees_accounting_product_id: Optional Product ID this Balance Fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Balance amount. Options are:

              - `"MINIMUM_SPEND"`
              - `"STANDING_CHARGE"`
              - `"USAGE"`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Balance amount at billing.

          name: The official name for the Balance.

          overage_description: A description for Bill line items overage charges.

          overage_surcharge_percent: Define a surcharge level, as a percentage of regular usage rating, applied to
              overages _(usage charges that exceed the Balance amount)_. For example, if the
              regular usage rate is $10 per unit of usage consumed and
              `overageSurchargePercent` is set at 10%, then any usage charged above the
              original Balance amount is charged at $11 per unit of usage.

          product_ids: Specify the Products whose consumption charges due at billing can be drawn-down
              against the Balance amount.

              **Note:** If you don't specify any Products for Balance draw-down, by default
              the consumption charges for any Product the Account consumes will be drawn-down
              against the Balance amount.

          rollover_amount: The maximum amount that can be carried over past the Balance end date for
              draw-down at billing if there is any unused Balance amount when the end date is
              reached. Works with `rolloverEndDate` to define the amount and duration of a
              Balance "grace period". _(Optional)_

              **Notes:**

              - If you leave `rolloverAmount` empty and only enter a `rolloverEndDate`, any
                amount left over after the Balance end date is reached will be drawn-down
                against up to the specified `rolloverEndDate`.
              - You must enter a `rolloverEndDate`. If you only enter a `rolloverAmount`
                without entering a `rolloverEndDate`, you'll receive an error when trying to
                create or update the Balance.
              - If you don't want to grant any grace period for outstanding Balance amounts,
                then do not use `rolloverAmount` and `rolloverEndDate`.

          rollover_end_date: The end date _(in ISO 8601 format)_ for the grace period during which unused
              Balance amounts can be carried over and drawn-down against at billing.

              **Note:** Use `rolloverAmount` if you want to specify a maximum amount that can
              be carried over and made available for draw-down.

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
            f"/organizations/{org_id}/balances",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "balance_draw_down_description": balance_draw_down_description,
                    "code": code,
                    "consumptions_accounting_product_id": consumptions_accounting_product_id,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "description": description,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "name": name,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "rollover_amount": rollover_amount,
                    "rollover_end_date": rollover_end_date,
                    "version": version,
                },
                balance_create_params.BalanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
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
    ) -> Balance:
        """
        Retrieve a specific Balance.

        This endpoint returns the details of the specified Balance.

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
            f"/organizations/{org_id}/balances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        currency: str,
        end_date: Union[str, datetime],
        start_date: Union[str, datetime],
        balance_draw_down_description: str | Omit = omit,
        code: str | Omit = omit,
        consumptions_accounting_product_id: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ]
        | Omit = omit,
        name: str | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        rollover_amount: float | Omit = omit,
        rollover_end_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Balance:
        """
        Update a specific Balance.

        This endpoint allows you to update the details of a specific Balance. The
        updated Balance details should be provided in the request body.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account.

          currency: The currency code used for the Balance amount. For example: USD, GBP or EUR.

          end_date: The date _(in ISO 8601 format)_ after which the Balance will no longer be active
              for the Account.

              **Note:** You can use the `rolloverEndDate` request parameter to define an
              extended grace period for continued draw-down against the Balance if any amount
              remains when the specified `endDate` is reached.

          start_date: The date _(in ISO 8601 format)_ when the Balance becomes active.

          balance_draw_down_description: A description for the bill line items for draw-down charges against the Balance.
              _(Optional)._

          code: Unique short code for the Balance.

          consumptions_accounting_product_id: Optional Product ID this Balance Consumptions should be attributed to for
              accounting purposes

          contract_id

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: A description of the Balance.

          fees_accounting_product_id: Optional Product ID this Balance Fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Balance amount. Options are:

              - `"MINIMUM_SPEND"`
              - `"STANDING_CHARGE"`
              - `"USAGE"`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Balance amount at billing.

          name: The official name for the Balance.

          overage_description: A description for Bill line items overage charges.

          overage_surcharge_percent: Define a surcharge level, as a percentage of regular usage rating, applied to
              overages _(usage charges that exceed the Balance amount)_. For example, if the
              regular usage rate is $10 per unit of usage consumed and
              `overageSurchargePercent` is set at 10%, then any usage charged above the
              original Balance amount is charged at $11 per unit of usage.

          product_ids: Specify the Products whose consumption charges due at billing can be drawn-down
              against the Balance amount.

              **Note:** If you don't specify any Products for Balance draw-down, by default
              the consumption charges for any Product the Account consumes will be drawn-down
              against the Balance amount.

          rollover_amount: The maximum amount that can be carried over past the Balance end date for
              draw-down at billing if there is any unused Balance amount when the end date is
              reached. Works with `rolloverEndDate` to define the amount and duration of a
              Balance "grace period". _(Optional)_

              **Notes:**

              - If you leave `rolloverAmount` empty and only enter a `rolloverEndDate`, any
                amount left over after the Balance end date is reached will be drawn-down
                against up to the specified `rolloverEndDate`.
              - You must enter a `rolloverEndDate`. If you only enter a `rolloverAmount`
                without entering a `rolloverEndDate`, you'll receive an error when trying to
                create or update the Balance.
              - If you don't want to grant any grace period for outstanding Balance amounts,
                then do not use `rolloverAmount` and `rolloverEndDate`.

          rollover_end_date: The end date _(in ISO 8601 format)_ for the grace period during which unused
              Balance amounts can be carried over and drawn-down against at billing.

              **Note:** Use `rolloverAmount` if you want to specify a maximum amount that can
              be carried over and made available for draw-down.

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
            f"/organizations/{org_id}/balances/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "balance_draw_down_description": balance_draw_down_description,
                    "code": code,
                    "consumptions_accounting_product_id": consumptions_accounting_product_id,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "description": description,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "name": name,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "rollover_amount": rollover_amount,
                    "rollover_end_date": rollover_end_date,
                    "version": version,
                },
                balance_update_params.BalanceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        contract: Optional[str] | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[Balance]:
        """
        Retrieve a list of all Balances for your Organization.

        This endpoint returns a list of all Balances associated with your organization.
        You can filter the Balances by the end customer's Account UUID and end dates,
        and paginate through them using the `pageSize` and `nextToken` parameters.

        **NOTE:** If a Balance has a rollover amount configured and you want to use the
        `endDateStart` or `endDateEnd` query parameters, the `rolloverEndDate` is used
        as the end date for the Balance.

        Args:
          account_id: The unique identifier (UUID) for the end customer's account.

          end_date_end: Only include Balances with end dates earlier than this date. If a Balance has a
              rollover amount configured, then the `rolloverEndDate` will be used as the end
              date.

          end_date_start: Only include Balances with end dates equal to or later than this date. If a
              Balance has a rollover amount configured, then the `rolloverEndDate` will be
              used as the end date.

          next_token: The `nextToken` for retrieving the next page of Balances. It is used to fetch
              the next page of Balances in a paginated list.

          page_size: The maximum number of Balances to return per page.

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
            f"/organizations/{org_id}/balances",
            page=SyncCursor[Balance],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "contract": contract,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    balance_list_params.BalanceListParams,
                ),
            ),
            model=Balance,
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
    ) -> Balance:
        """
        Delete a specific Balance.

        This endpoint allows you to delete a specific Balance with the given UUID.

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
            f"/organizations/{org_id}/balances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )


class AsyncBalancesResource(AsyncAPIResource):
    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        return AsyncTransactionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncBalancesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncBalancesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBalancesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncBalancesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        currency: str,
        end_date: Union[str, datetime],
        start_date: Union[str, datetime],
        balance_draw_down_description: str | Omit = omit,
        code: str | Omit = omit,
        consumptions_accounting_product_id: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ]
        | Omit = omit,
        name: str | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        rollover_amount: float | Omit = omit,
        rollover_end_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Balance:
        """
        Create a new Balance for the given end customer Account.

        This endpoint allows you to create a new Balance for a specific end customer
        Account. The Balance details should be provided in the request body.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account.

          currency: The currency code used for the Balance amount. For example: USD, GBP or EUR.

          end_date: The date _(in ISO 8601 format)_ after which the Balance will no longer be active
              for the Account.

              **Note:** You can use the `rolloverEndDate` request parameter to define an
              extended grace period for continued draw-down against the Balance if any amount
              remains when the specified `endDate` is reached.

          start_date: The date _(in ISO 8601 format)_ when the Balance becomes active.

          balance_draw_down_description: A description for the bill line items for draw-down charges against the Balance.
              _(Optional)._

          code: Unique short code for the Balance.

          consumptions_accounting_product_id: Optional Product ID this Balance Consumptions should be attributed to for
              accounting purposes

          contract_id

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: A description of the Balance.

          fees_accounting_product_id: Optional Product ID this Balance Fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Balance amount. Options are:

              - `"MINIMUM_SPEND"`
              - `"STANDING_CHARGE"`
              - `"USAGE"`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Balance amount at billing.

          name: The official name for the Balance.

          overage_description: A description for Bill line items overage charges.

          overage_surcharge_percent: Define a surcharge level, as a percentage of regular usage rating, applied to
              overages _(usage charges that exceed the Balance amount)_. For example, if the
              regular usage rate is $10 per unit of usage consumed and
              `overageSurchargePercent` is set at 10%, then any usage charged above the
              original Balance amount is charged at $11 per unit of usage.

          product_ids: Specify the Products whose consumption charges due at billing can be drawn-down
              against the Balance amount.

              **Note:** If you don't specify any Products for Balance draw-down, by default
              the consumption charges for any Product the Account consumes will be drawn-down
              against the Balance amount.

          rollover_amount: The maximum amount that can be carried over past the Balance end date for
              draw-down at billing if there is any unused Balance amount when the end date is
              reached. Works with `rolloverEndDate` to define the amount and duration of a
              Balance "grace period". _(Optional)_

              **Notes:**

              - If you leave `rolloverAmount` empty and only enter a `rolloverEndDate`, any
                amount left over after the Balance end date is reached will be drawn-down
                against up to the specified `rolloverEndDate`.
              - You must enter a `rolloverEndDate`. If you only enter a `rolloverAmount`
                without entering a `rolloverEndDate`, you'll receive an error when trying to
                create or update the Balance.
              - If you don't want to grant any grace period for outstanding Balance amounts,
                then do not use `rolloverAmount` and `rolloverEndDate`.

          rollover_end_date: The end date _(in ISO 8601 format)_ for the grace period during which unused
              Balance amounts can be carried over and drawn-down against at billing.

              **Note:** Use `rolloverAmount` if you want to specify a maximum amount that can
              be carried over and made available for draw-down.

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
            f"/organizations/{org_id}/balances",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "balance_draw_down_description": balance_draw_down_description,
                    "code": code,
                    "consumptions_accounting_product_id": consumptions_accounting_product_id,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "description": description,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "name": name,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "rollover_amount": rollover_amount,
                    "rollover_end_date": rollover_end_date,
                    "version": version,
                },
                balance_create_params.BalanceCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
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
    ) -> Balance:
        """
        Retrieve a specific Balance.

        This endpoint returns the details of the specified Balance.

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
            f"/organizations/{org_id}/balances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        currency: str,
        end_date: Union[str, datetime],
        start_date: Union[str, datetime],
        balance_draw_down_description: str | Omit = omit,
        code: str | Omit = omit,
        consumptions_accounting_product_id: str | Omit = omit,
        contract_id: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        fees_accounting_product_id: str | Omit = omit,
        line_item_types: List[
            Literal[
                "STANDING_CHARGE",
                "USAGE",
                "MINIMUM_SPEND",
                "COUNTER_RUNNING_TOTAL_CHARGE",
                "COUNTER_ADJUSTMENT_DEBIT",
                "AD_HOC",
            ]
        ]
        | Omit = omit,
        name: str | Omit = omit,
        overage_description: str | Omit = omit,
        overage_surcharge_percent: float | Omit = omit,
        product_ids: SequenceNotStr[str] | Omit = omit,
        rollover_amount: float | Omit = omit,
        rollover_end_date: Union[str, datetime] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Balance:
        """
        Update a specific Balance.

        This endpoint allows you to update the details of a specific Balance. The
        updated Balance details should be provided in the request body.

        Args:
          account_id: The unique identifier (UUID) for the end customer Account.

          currency: The currency code used for the Balance amount. For example: USD, GBP or EUR.

          end_date: The date _(in ISO 8601 format)_ after which the Balance will no longer be active
              for the Account.

              **Note:** You can use the `rolloverEndDate` request parameter to define an
              extended grace period for continued draw-down against the Balance if any amount
              remains when the specified `endDate` is reached.

          start_date: The date _(in ISO 8601 format)_ when the Balance becomes active.

          balance_draw_down_description: A description for the bill line items for draw-down charges against the Balance.
              _(Optional)._

          code: Unique short code for the Balance.

          consumptions_accounting_product_id: Optional Product ID this Balance Consumptions should be attributed to for
              accounting purposes

          contract_id

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: A description of the Balance.

          fees_accounting_product_id: Optional Product ID this Balance Fees should be attributed to for accounting
              purposes

          line_item_types: Specify the line item charge types that can draw-down at billing against the
              Balance amount. Options are:

              - `"MINIMUM_SPEND"`
              - `"STANDING_CHARGE"`
              - `"USAGE"`
              - `"COUNTER_RUNNING_TOTAL_CHARGE"`
              - `"COUNTER_ADJUSTMENT_DEBIT"`

              **NOTE:** If no charge types are specified, by default _all types_ can draw-down
              against the Balance amount at billing.

          name: The official name for the Balance.

          overage_description: A description for Bill line items overage charges.

          overage_surcharge_percent: Define a surcharge level, as a percentage of regular usage rating, applied to
              overages _(usage charges that exceed the Balance amount)_. For example, if the
              regular usage rate is $10 per unit of usage consumed and
              `overageSurchargePercent` is set at 10%, then any usage charged above the
              original Balance amount is charged at $11 per unit of usage.

          product_ids: Specify the Products whose consumption charges due at billing can be drawn-down
              against the Balance amount.

              **Note:** If you don't specify any Products for Balance draw-down, by default
              the consumption charges for any Product the Account consumes will be drawn-down
              against the Balance amount.

          rollover_amount: The maximum amount that can be carried over past the Balance end date for
              draw-down at billing if there is any unused Balance amount when the end date is
              reached. Works with `rolloverEndDate` to define the amount and duration of a
              Balance "grace period". _(Optional)_

              **Notes:**

              - If you leave `rolloverAmount` empty and only enter a `rolloverEndDate`, any
                amount left over after the Balance end date is reached will be drawn-down
                against up to the specified `rolloverEndDate`.
              - You must enter a `rolloverEndDate`. If you only enter a `rolloverAmount`
                without entering a `rolloverEndDate`, you'll receive an error when trying to
                create or update the Balance.
              - If you don't want to grant any grace period for outstanding Balance amounts,
                then do not use `rolloverAmount` and `rolloverEndDate`.

          rollover_end_date: The end date _(in ISO 8601 format)_ for the grace period during which unused
              Balance amounts can be carried over and drawn-down against at billing.

              **Note:** Use `rolloverAmount` if you want to specify a maximum amount that can
              be carried over and made available for draw-down.

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
            f"/organizations/{org_id}/balances/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "currency": currency,
                    "end_date": end_date,
                    "start_date": start_date,
                    "balance_draw_down_description": balance_draw_down_description,
                    "code": code,
                    "consumptions_accounting_product_id": consumptions_accounting_product_id,
                    "contract_id": contract_id,
                    "custom_fields": custom_fields,
                    "description": description,
                    "fees_accounting_product_id": fees_accounting_product_id,
                    "line_item_types": line_item_types,
                    "name": name,
                    "overage_description": overage_description,
                    "overage_surcharge_percent": overage_surcharge_percent,
                    "product_ids": product_ids,
                    "rollover_amount": rollover_amount,
                    "rollover_end_date": rollover_end_date,
                    "version": version,
                },
                balance_update_params.BalanceUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        contract: Optional[str] | Omit = omit,
        end_date_end: str | Omit = omit,
        end_date_start: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[Balance, AsyncCursor[Balance]]:
        """
        Retrieve a list of all Balances for your Organization.

        This endpoint returns a list of all Balances associated with your organization.
        You can filter the Balances by the end customer's Account UUID and end dates,
        and paginate through them using the `pageSize` and `nextToken` parameters.

        **NOTE:** If a Balance has a rollover amount configured and you want to use the
        `endDateStart` or `endDateEnd` query parameters, the `rolloverEndDate` is used
        as the end date for the Balance.

        Args:
          account_id: The unique identifier (UUID) for the end customer's account.

          end_date_end: Only include Balances with end dates earlier than this date. If a Balance has a
              rollover amount configured, then the `rolloverEndDate` will be used as the end
              date.

          end_date_start: Only include Balances with end dates equal to or later than this date. If a
              Balance has a rollover amount configured, then the `rolloverEndDate` will be
              used as the end date.

          next_token: The `nextToken` for retrieving the next page of Balances. It is used to fetch
              the next page of Balances in a paginated list.

          page_size: The maximum number of Balances to return per page.

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
            f"/organizations/{org_id}/balances",
            page=AsyncCursor[Balance],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "contract": contract,
                        "end_date_end": end_date_end,
                        "end_date_start": end_date_start,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    balance_list_params.BalanceListParams,
                ),
            ),
            model=Balance,
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
    ) -> Balance:
        """
        Delete a specific Balance.

        This endpoint allows you to delete a specific Balance with the given UUID.

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
            f"/organizations/{org_id}/balances/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Balance,
        )


class BalancesResourceWithRawResponse:
    def __init__(self, balances: BalancesResource) -> None:
        self._balances = balances

        self.create = to_raw_response_wrapper(
            balances.create,
        )
        self.retrieve = to_raw_response_wrapper(
            balances.retrieve,
        )
        self.update = to_raw_response_wrapper(
            balances.update,
        )
        self.list = to_raw_response_wrapper(
            balances.list,
        )
        self.delete = to_raw_response_wrapper(
            balances.delete,
        )

    @cached_property
    def transactions(self) -> TransactionsResourceWithRawResponse:
        return TransactionsResourceWithRawResponse(self._balances.transactions)


class AsyncBalancesResourceWithRawResponse:
    def __init__(self, balances: AsyncBalancesResource) -> None:
        self._balances = balances

        self.create = async_to_raw_response_wrapper(
            balances.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            balances.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            balances.update,
        )
        self.list = async_to_raw_response_wrapper(
            balances.list,
        )
        self.delete = async_to_raw_response_wrapper(
            balances.delete,
        )

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithRawResponse:
        return AsyncTransactionsResourceWithRawResponse(self._balances.transactions)


class BalancesResourceWithStreamingResponse:
    def __init__(self, balances: BalancesResource) -> None:
        self._balances = balances

        self.create = to_streamed_response_wrapper(
            balances.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            balances.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            balances.update,
        )
        self.list = to_streamed_response_wrapper(
            balances.list,
        )
        self.delete = to_streamed_response_wrapper(
            balances.delete,
        )

    @cached_property
    def transactions(self) -> TransactionsResourceWithStreamingResponse:
        return TransactionsResourceWithStreamingResponse(self._balances.transactions)


class AsyncBalancesResourceWithStreamingResponse:
    def __init__(self, balances: AsyncBalancesResource) -> None:
        self._balances = balances

        self.create = async_to_streamed_response_wrapper(
            balances.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            balances.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            balances.update,
        )
        self.list = async_to_streamed_response_wrapper(
            balances.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            balances.delete,
        )

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithStreamingResponse:
        return AsyncTransactionsResourceWithStreamingResponse(self._balances.transactions)
