# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

from ...types import (
    bill_list_params,
    bill_search_params,
    bill_approve_params,
    bill_retrieve_params,
    bill_update_status_params,
    bill_latest_by_account_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .line_items import (
    LineItemsResource,
    AsyncLineItemsResource,
    LineItemsResourceWithRawResponse,
    AsyncLineItemsResourceWithRawResponse,
    LineItemsResourceWithStreamingResponse,
    AsyncLineItemsResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...pagination import SyncCursor, AsyncCursor
from ..._base_client import AsyncPaginator, make_request_options
from .debit_line_items import (
    DebitLineItemsResource,
    AsyncDebitLineItemsResource,
    DebitLineItemsResourceWithRawResponse,
    AsyncDebitLineItemsResourceWithRawResponse,
    DebitLineItemsResourceWithStreamingResponse,
    AsyncDebitLineItemsResourceWithStreamingResponse,
)
from .credit_line_items import (
    CreditLineItemsResource,
    AsyncCreditLineItemsResource,
    CreditLineItemsResourceWithRawResponse,
    AsyncCreditLineItemsResourceWithRawResponse,
    CreditLineItemsResourceWithStreamingResponse,
    AsyncCreditLineItemsResourceWithStreamingResponse,
)
from ...types.bill_response import BillResponse
from ...types.bill_search_response import BillSearchResponse
from ...types.bill_approve_response import BillApproveResponse

__all__ = ["BillsResource", "AsyncBillsResource"]


class BillsResource(SyncAPIResource):
    @cached_property
    def credit_line_items(self) -> CreditLineItemsResource:
        return CreditLineItemsResource(self._client)

    @cached_property
    def debit_line_items(self) -> DebitLineItemsResource:
        return DebitLineItemsResource(self._client)

    @cached_property
    def line_items(self) -> LineItemsResource:
        return LineItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> BillsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return BillsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BillsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return BillsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Retrieve the Bill with the given UUID.

        This endpoint retrieves the Bill with the given unique identifier (UUID) and
        specific Organization.

        Args:
          additional: Comma separated list of additional fields.

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
            f"/organizations/{org_id}/bills/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"additional": additional}, bill_retrieve_params.BillRetrieveParams),
            ),
            cast_to=BillResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        additional: SequenceNotStr[str] | Omit = omit,
        bill_date: str | Omit = omit,
        bill_date_end: str | Omit = omit,
        bill_date_start: str | Omit = omit,
        billing_frequency: Optional[str] | Omit = omit,
        exclude_line_items: bool | Omit = omit,
        external_invoice_date_end: str | Omit = omit,
        external_invoice_date_start: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        include_bill_total: bool | Omit = omit,
        locked: bool | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: Literal["PENDING", "APPROVED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[BillResponse]:
        """
        Retrieve a list of Bills.

        This endpoint retrieves a list of all Bills for the given Account within the
        specified Organization. Optional filters can be applied such as by date range,
        lock status, or other attributes. The list can also be paginated for easier
        management.

        Args:
          account_id: Optional filter. An Account ID - returns the Bills for the single specified
              Account.

          additional: Comma separated list of additional fields.

          bill_date: The specific date in ISO 8601 format for which you want to retrieve Bills.

          bill_date_end: Only include Bills with bill dates earlier than this date.

          bill_date_start: Only include Bills with bill dates equal to or later than this date.

          exclude_line_items: Exclude Line Items

          external_invoice_date_end: Only include Bills with external invoice dates earlier than this date.

          external_invoice_date_start: Only include Bills with external invoice dates equal to or later than this date.

          ids: Optional filter. The list of Bill IDs to retrieve.

          include_bill_total: Include Bill Total

          locked: Boolean flag specifying whether to include Bills with "locked" status.

              - **TRUE** - the list inlcudes "locked" Bills.
              - **FALSE** - excludes "locked" Bills from the list.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Bills in a paginated list.

          page_size: Specifies the maximum number of Bills to retrieve per page.

          status: Only include Bills having the given status

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
            f"/organizations/{org_id}/bills",
            page=SyncCursor[BillResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "additional": additional,
                        "bill_date": bill_date,
                        "bill_date_end": bill_date_end,
                        "bill_date_start": bill_date_start,
                        "billing_frequency": billing_frequency,
                        "exclude_line_items": exclude_line_items,
                        "external_invoice_date_end": external_invoice_date_end,
                        "external_invoice_date_start": external_invoice_date_start,
                        "ids": ids,
                        "include_bill_total": include_bill_total,
                        "locked": locked,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    bill_list_params.BillListParams,
                ),
            ),
            model=BillResponse,
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
    ) -> BillResponse:
        """
        Delete the Bill with the given UUID.

        This endpoint deletes the specified Bill with the given unique identifier. Use
        with caution since deleted Bills cannot be recovered. Suitable for removing
        incorrect or obsolete Bills, and for Bills that have not been sent to customers.
        Where end-customer invoices for Bills have been sent to customers, Bills should
        not be deleted to ensure you have an audit trail of how the invoice was created.

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
            f"/organizations/{org_id}/bills/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
        )

    def approve(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        account_ids: str | Omit = omit,
        external_invoice_date_end: str | Omit = omit,
        external_invoice_date_start: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillApproveResponse:
        """
        Approve multiple Bills for the specified Organization based on the given
        criteria.

        This endpoint allows you to change currently _Pending_ Bills to _Approved_
        status for further processing.

        Query Parameters:

        - Use `accountIds` to approve Bills for specifed Accounts.

        Request Body Schema Parameter:

        - Use `billIds` to specify a collection of Bills for batch approval.

        **Important!** If you use the `billIds` Request Body Schema parameter, any Query
        parameters you might have also used are ignored when the call is processed.

        Args:
          bill_ids: Use to specify a collection of Bills by their IDs for batch approval

          account_ids: List of Account IDs to filter Bills. This allows you to approve Bills for
              specific Accounts within the Organization.

          external_invoice_date_end: End date for filtering Bills by external invoice date. Includes Bills with dates
              earlier than this date.

          external_invoice_date_start: Start date for filtering Bills by external invoice date. Includes Bills with
              dates equal to or later than this date.

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
            f"/organizations/{org_id}/bills/approve",
            body=maybe_transform({"bill_ids": bill_ids}, bill_approve_params.BillApproveParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_ids": account_ids,
                        "external_invoice_date_end": external_invoice_date_end,
                        "external_invoice_date_start": external_invoice_date_start,
                    },
                    bill_approve_params.BillApproveParams,
                ),
            ),
            cast_to=BillApproveResponse,
        )

    def latest_by_account(
        self,
        account_id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Retrieve the latest Bill for the given Account.

        This endpoint retrieves the latest Bill for the given Account in the specified
        Organization. It facilitates tracking of the most recent charges and consumption
        details.

        Args:
          additional: Comma separated list of additional fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/organizations/{org_id}/bills/latest/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"additional": additional}, bill_latest_by_account_params.BillLatestByAccountParams
                ),
            ),
            cast_to=BillResponse,
        )

    def lock(
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
    ) -> BillResponse:
        """Lock the specific Bill identified by the given UUID.

        Once a Bill is locked, no
        further changes can be made to it.

        **NOTE:** You cannot lock a Bill whose current status is `PENDING`. You will
        receive an error message if you try to do this. You must first use the
        [Approve Bills](https://www.m3ter.com/docs/api#tag/Bill/operation/ApproveBills)
        call to approve a Bill before you can lock it.

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
        return self._put(
            f"/organizations/{org_id}/bills/{id}/lock",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
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
    ) -> BillSearchResponse:
        """
        Search for Bill entities.

        This endpoint executes a search query for Bills based on the user specified
        search criteria. The search query is customizable, allowing for complex nested
        conditions and sorting. The returned list of Bills can be paginated for easier
        management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Bills to retrieve per page.

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
              - Allowed parameters: accountId, locked, billDate, startDate, endDate, dueDate,
                billingFrequency, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=startDate>2023-01-01$accountId:62eaad67-5790-407e-b853-881564f0e543.
                - This query is translated into: find Bills that startDate is older than
                  2023-01-01 AND accountId is equal to 62eaad67-5790-407e-b853-881564f0e543.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Bill entity to sort by, such as `accountId`, `endDate`, and so on.

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
            f"/organizations/{org_id}/bills/search",
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
                    bill_search_params.BillSearchParams,
                ),
            ),
            cast_to=BillSearchResponse,
        )

    def update_status(
        self,
        id: str,
        *,
        org_id: str | None = None,
        status: Literal["PENDING", "APPROVED"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Updates the status of a specified Bill with the given Bill ID.

        This endpoint allows you to transition a Bill's status through various stages,
        such as from "Pending" to "Approved".

        Args:
          status: The new status you want to assign to the Bill. Must be one "Pending" or
              "Approved".

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
            f"/organizations/{org_id}/bills/{id}/status",
            body=maybe_transform({"status": status}, bill_update_status_params.BillUpdateStatusParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
        )


class AsyncBillsResource(AsyncAPIResource):
    @cached_property
    def credit_line_items(self) -> AsyncCreditLineItemsResource:
        return AsyncCreditLineItemsResource(self._client)

    @cached_property
    def debit_line_items(self) -> AsyncDebitLineItemsResource:
        return AsyncDebitLineItemsResource(self._client)

    @cached_property
    def line_items(self) -> AsyncLineItemsResource:
        return AsyncLineItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncBillsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncBillsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBillsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncBillsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Retrieve the Bill with the given UUID.

        This endpoint retrieves the Bill with the given unique identifier (UUID) and
        specific Organization.

        Args:
          additional: Comma separated list of additional fields.

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
            f"/organizations/{org_id}/bills/{id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"additional": additional}, bill_retrieve_params.BillRetrieveParams),
            ),
            cast_to=BillResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: str | Omit = omit,
        additional: SequenceNotStr[str] | Omit = omit,
        bill_date: str | Omit = omit,
        bill_date_end: str | Omit = omit,
        bill_date_start: str | Omit = omit,
        billing_frequency: Optional[str] | Omit = omit,
        exclude_line_items: bool | Omit = omit,
        external_invoice_date_end: str | Omit = omit,
        external_invoice_date_start: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        include_bill_total: bool | Omit = omit,
        locked: bool | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        status: Literal["PENDING", "APPROVED"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[BillResponse, AsyncCursor[BillResponse]]:
        """
        Retrieve a list of Bills.

        This endpoint retrieves a list of all Bills for the given Account within the
        specified Organization. Optional filters can be applied such as by date range,
        lock status, or other attributes. The list can also be paginated for easier
        management.

        Args:
          account_id: Optional filter. An Account ID - returns the Bills for the single specified
              Account.

          additional: Comma separated list of additional fields.

          bill_date: The specific date in ISO 8601 format for which you want to retrieve Bills.

          bill_date_end: Only include Bills with bill dates earlier than this date.

          bill_date_start: Only include Bills with bill dates equal to or later than this date.

          exclude_line_items: Exclude Line Items

          external_invoice_date_end: Only include Bills with external invoice dates earlier than this date.

          external_invoice_date_start: Only include Bills with external invoice dates equal to or later than this date.

          ids: Optional filter. The list of Bill IDs to retrieve.

          include_bill_total: Include Bill Total

          locked: Boolean flag specifying whether to include Bills with "locked" status.

              - **TRUE** - the list inlcudes "locked" Bills.
              - **FALSE** - excludes "locked" Bills from the list.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Bills in a paginated list.

          page_size: Specifies the maximum number of Bills to retrieve per page.

          status: Only include Bills having the given status

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
            f"/organizations/{org_id}/bills",
            page=AsyncCursor[BillResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "additional": additional,
                        "bill_date": bill_date,
                        "bill_date_end": bill_date_end,
                        "bill_date_start": bill_date_start,
                        "billing_frequency": billing_frequency,
                        "exclude_line_items": exclude_line_items,
                        "external_invoice_date_end": external_invoice_date_end,
                        "external_invoice_date_start": external_invoice_date_start,
                        "ids": ids,
                        "include_bill_total": include_bill_total,
                        "locked": locked,
                        "next_token": next_token,
                        "page_size": page_size,
                        "status": status,
                    },
                    bill_list_params.BillListParams,
                ),
            ),
            model=BillResponse,
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
    ) -> BillResponse:
        """
        Delete the Bill with the given UUID.

        This endpoint deletes the specified Bill with the given unique identifier. Use
        with caution since deleted Bills cannot be recovered. Suitable for removing
        incorrect or obsolete Bills, and for Bills that have not been sent to customers.
        Where end-customer invoices for Bills have been sent to customers, Bills should
        not be deleted to ensure you have an audit trail of how the invoice was created.

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
            f"/organizations/{org_id}/bills/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
        )

    async def approve(
        self,
        *,
        org_id: str | None = None,
        bill_ids: SequenceNotStr[str],
        account_ids: str | Omit = omit,
        external_invoice_date_end: str | Omit = omit,
        external_invoice_date_start: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillApproveResponse:
        """
        Approve multiple Bills for the specified Organization based on the given
        criteria.

        This endpoint allows you to change currently _Pending_ Bills to _Approved_
        status for further processing.

        Query Parameters:

        - Use `accountIds` to approve Bills for specifed Accounts.

        Request Body Schema Parameter:

        - Use `billIds` to specify a collection of Bills for batch approval.

        **Important!** If you use the `billIds` Request Body Schema parameter, any Query
        parameters you might have also used are ignored when the call is processed.

        Args:
          bill_ids: Use to specify a collection of Bills by their IDs for batch approval

          account_ids: List of Account IDs to filter Bills. This allows you to approve Bills for
              specific Accounts within the Organization.

          external_invoice_date_end: End date for filtering Bills by external invoice date. Includes Bills with dates
              earlier than this date.

          external_invoice_date_start: Start date for filtering Bills by external invoice date. Includes Bills with
              dates equal to or later than this date.

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
            f"/organizations/{org_id}/bills/approve",
            body=await async_maybe_transform({"bill_ids": bill_ids}, bill_approve_params.BillApproveParams),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "account_ids": account_ids,
                        "external_invoice_date_end": external_invoice_date_end,
                        "external_invoice_date_start": external_invoice_date_start,
                    },
                    bill_approve_params.BillApproveParams,
                ),
            ),
            cast_to=BillApproveResponse,
        )

    async def latest_by_account(
        self,
        account_id: str,
        *,
        org_id: str | None = None,
        additional: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Retrieve the latest Bill for the given Account.

        This endpoint retrieves the latest Bill for the given Account in the specified
        Organization. It facilitates tracking of the most recent charges and consumption
        details.

        Args:
          additional: Comma separated list of additional fields.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/organizations/{org_id}/bills/latest/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"additional": additional}, bill_latest_by_account_params.BillLatestByAccountParams
                ),
            ),
            cast_to=BillResponse,
        )

    async def lock(
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
    ) -> BillResponse:
        """Lock the specific Bill identified by the given UUID.

        Once a Bill is locked, no
        further changes can be made to it.

        **NOTE:** You cannot lock a Bill whose current status is `PENDING`. You will
        receive an error message if you try to do this. You must first use the
        [Approve Bills](https://www.m3ter.com/docs/api#tag/Bill/operation/ApproveBills)
        call to approve a Bill before you can lock it.

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
        return await self._put(
            f"/organizations/{org_id}/bills/{id}/lock",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
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
    ) -> BillSearchResponse:
        """
        Search for Bill entities.

        This endpoint executes a search query for Bills based on the user specified
        search criteria. The search query is customizable, allowing for complex nested
        conditions and sorting. The returned list of Bills can be paginated for easier
        management.

        Args:
          from_document: `fromDocument` for multi page retrievals.

          operator: Search Operator to be used while querying search.

          page_size: Number of Bills to retrieve per page.

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
              - Allowed parameters: accountId, locked, billDate, startDate, endDate, dueDate,
                billingFrequency, id, createdBy, dtCreated, lastModifiedBy, ids.
              - Query example:
                - searchQuery=startDate>2023-01-01$accountId:62eaad67-5790-407e-b853-881564f0e543.
                - This query is translated into: find Bills that startDate is older than
                  2023-01-01 AND accountId is equal to 62eaad67-5790-407e-b853-881564f0e543.

              **Note:** Using the ~ match phrase/prefix comparator. For best results, we
              recommend treating this as a "starts with" comparator for your search query.

          sort_by: Name of the parameter on which sorting is performed. Use any field available on
              the Bill entity to sort by, such as `accountId`, `endDate`, and so on.

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
            f"/organizations/{org_id}/bills/search",
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
                    bill_search_params.BillSearchParams,
                ),
            ),
            cast_to=BillSearchResponse,
        )

    async def update_status(
        self,
        id: str,
        *,
        org_id: str | None = None,
        status: Literal["PENDING", "APPROVED"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BillResponse:
        """
        Updates the status of a specified Bill with the given Bill ID.

        This endpoint allows you to transition a Bill's status through various stages,
        such as from "Pending" to "Approved".

        Args:
          status: The new status you want to assign to the Bill. Must be one "Pending" or
              "Approved".

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
            f"/organizations/{org_id}/bills/{id}/status",
            body=await async_maybe_transform({"status": status}, bill_update_status_params.BillUpdateStatusParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BillResponse,
        )


class BillsResourceWithRawResponse:
    def __init__(self, bills: BillsResource) -> None:
        self._bills = bills

        self.retrieve = to_raw_response_wrapper(
            bills.retrieve,
        )
        self.list = to_raw_response_wrapper(
            bills.list,
        )
        self.delete = to_raw_response_wrapper(
            bills.delete,
        )
        self.approve = to_raw_response_wrapper(
            bills.approve,
        )
        self.latest_by_account = to_raw_response_wrapper(
            bills.latest_by_account,
        )
        self.lock = to_raw_response_wrapper(
            bills.lock,
        )
        self.search = to_raw_response_wrapper(
            bills.search,
        )
        self.update_status = to_raw_response_wrapper(
            bills.update_status,
        )

    @cached_property
    def credit_line_items(self) -> CreditLineItemsResourceWithRawResponse:
        return CreditLineItemsResourceWithRawResponse(self._bills.credit_line_items)

    @cached_property
    def debit_line_items(self) -> DebitLineItemsResourceWithRawResponse:
        return DebitLineItemsResourceWithRawResponse(self._bills.debit_line_items)

    @cached_property
    def line_items(self) -> LineItemsResourceWithRawResponse:
        return LineItemsResourceWithRawResponse(self._bills.line_items)


class AsyncBillsResourceWithRawResponse:
    def __init__(self, bills: AsyncBillsResource) -> None:
        self._bills = bills

        self.retrieve = async_to_raw_response_wrapper(
            bills.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            bills.list,
        )
        self.delete = async_to_raw_response_wrapper(
            bills.delete,
        )
        self.approve = async_to_raw_response_wrapper(
            bills.approve,
        )
        self.latest_by_account = async_to_raw_response_wrapper(
            bills.latest_by_account,
        )
        self.lock = async_to_raw_response_wrapper(
            bills.lock,
        )
        self.search = async_to_raw_response_wrapper(
            bills.search,
        )
        self.update_status = async_to_raw_response_wrapper(
            bills.update_status,
        )

    @cached_property
    def credit_line_items(self) -> AsyncCreditLineItemsResourceWithRawResponse:
        return AsyncCreditLineItemsResourceWithRawResponse(self._bills.credit_line_items)

    @cached_property
    def debit_line_items(self) -> AsyncDebitLineItemsResourceWithRawResponse:
        return AsyncDebitLineItemsResourceWithRawResponse(self._bills.debit_line_items)

    @cached_property
    def line_items(self) -> AsyncLineItemsResourceWithRawResponse:
        return AsyncLineItemsResourceWithRawResponse(self._bills.line_items)


class BillsResourceWithStreamingResponse:
    def __init__(self, bills: BillsResource) -> None:
        self._bills = bills

        self.retrieve = to_streamed_response_wrapper(
            bills.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            bills.list,
        )
        self.delete = to_streamed_response_wrapper(
            bills.delete,
        )
        self.approve = to_streamed_response_wrapper(
            bills.approve,
        )
        self.latest_by_account = to_streamed_response_wrapper(
            bills.latest_by_account,
        )
        self.lock = to_streamed_response_wrapper(
            bills.lock,
        )
        self.search = to_streamed_response_wrapper(
            bills.search,
        )
        self.update_status = to_streamed_response_wrapper(
            bills.update_status,
        )

    @cached_property
    def credit_line_items(self) -> CreditLineItemsResourceWithStreamingResponse:
        return CreditLineItemsResourceWithStreamingResponse(self._bills.credit_line_items)

    @cached_property
    def debit_line_items(self) -> DebitLineItemsResourceWithStreamingResponse:
        return DebitLineItemsResourceWithStreamingResponse(self._bills.debit_line_items)

    @cached_property
    def line_items(self) -> LineItemsResourceWithStreamingResponse:
        return LineItemsResourceWithStreamingResponse(self._bills.line_items)


class AsyncBillsResourceWithStreamingResponse:
    def __init__(self, bills: AsyncBillsResource) -> None:
        self._bills = bills

        self.retrieve = async_to_streamed_response_wrapper(
            bills.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            bills.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            bills.delete,
        )
        self.approve = async_to_streamed_response_wrapper(
            bills.approve,
        )
        self.latest_by_account = async_to_streamed_response_wrapper(
            bills.latest_by_account,
        )
        self.lock = async_to_streamed_response_wrapper(
            bills.lock,
        )
        self.search = async_to_streamed_response_wrapper(
            bills.search,
        )
        self.update_status = async_to_streamed_response_wrapper(
            bills.update_status,
        )

    @cached_property
    def credit_line_items(self) -> AsyncCreditLineItemsResourceWithStreamingResponse:
        return AsyncCreditLineItemsResourceWithStreamingResponse(self._bills.credit_line_items)

    @cached_property
    def debit_line_items(self) -> AsyncDebitLineItemsResourceWithStreamingResponse:
        return AsyncDebitLineItemsResourceWithStreamingResponse(self._bills.debit_line_items)

    @cached_property
    def line_items(self) -> AsyncLineItemsResourceWithStreamingResponse:
        return AsyncLineItemsResourceWithStreamingResponse(self._bills.line_items)
