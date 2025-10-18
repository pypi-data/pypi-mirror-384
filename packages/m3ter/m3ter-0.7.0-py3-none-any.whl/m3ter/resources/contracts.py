# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, List, Union, Optional
from datetime import date, datetime
from typing_extensions import Literal

import httpx

from ..types import (
    contract_list_params,
    contract_create_params,
    contract_update_params,
    contract_end_date_billing_entities_params,
)
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
from ..types.contract_response import ContractResponse
from ..types.contract_end_date_billing_entities_response import ContractEndDateBillingEntitiesResponse

__all__ = ["ContractsResource", "AsyncContractsResource"]


class ContractsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ContractsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ContractsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ContractsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ContractsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        end_date: Union[str, date],
        name: str,
        start_date: Union[str, date],
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractResponse:
        """Create a new Contract.

        Creates a new Contract for the specified Account.

        The Contract includes
        information such as the associated Account along with start and end dates.

        Args:
          account_id: The unique identifier (UUID) of the Account associated with this Contract.

          end_date: The exclusive end date of the Contract _(in ISO-8601 format)_. This means the
              Contract is active until midnight on the day **_before_** this date.

          name: The name of the Contract.

          start_date: The start date for the Contract _(in ISO-8601 format)_. This date is inclusive,
              meaning the Contract is active from this date onward.

          code: The short code of the Contract.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: The description of the Contract, which provides context and information.

          purchase_order_number: The Purchase Order Number associated with the Contract.

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
            f"/organizations/{org_id}/contracts",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "end_date": end_date,
                    "name": name,
                    "start_date": start_date,
                    "code": code,
                    "custom_fields": custom_fields,
                    "description": description,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                contract_create_params.ContractCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
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
    ) -> ContractResponse:
        """Retrieves the Contract with the given UUID.

        Used to obtain the details of a
        Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        end_date: Union[str, date],
        name: str,
        start_date: Union[str, date],
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractResponse:
        """
        Update the Contract with the given UUID.

        This endpoint updates the details of the Contract with the specified ID. Used to
        modify details of an existing Contract such as the start or end dates.

        **Note:** If you have created Custom Fields for a Contract, when you use this
        endpoint to update the Contract use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          account_id: The unique identifier (UUID) of the Account associated with this Contract.

          end_date: The exclusive end date of the Contract _(in ISO-8601 format)_. This means the
              Contract is active until midnight on the day **_before_** this date.

          name: The name of the Contract.

          start_date: The start date for the Contract _(in ISO-8601 format)_. This date is inclusive,
              meaning the Contract is active from this date onward.

          code: The short code of the Contract.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: The description of the Contract, which provides context and information.

          purchase_order_number: The Purchase Order Number associated with the Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            body=maybe_transform(
                {
                    "account_id": account_id,
                    "end_date": end_date,
                    "name": name,
                    "start_date": start_date,
                    "code": code,
                    "custom_fields": custom_fields,
                    "description": description,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                contract_update_params.ContractUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: Optional[str] | Omit = omit,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ContractResponse]:
        """Retrieves a list of Contracts by Organization ID.

        Supports pagination and
        includes various query parameters to filter the Contracts returned based on
        Contract IDs or short codes.

        Args:
          codes: An optional parameter to retrieve specific Contracts based on their short codes.

          ids: An optional parameter to filter the list based on specific Contract unique
              identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Contracts in a paginated list.

          page_size: Specifies the maximum number of Contracts to retrieve per page.

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
            f"/organizations/{org_id}/contracts",
            page=SyncCursor[ContractResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    contract_list_params.ContractListParams,
                ),
            ),
            model=ContractResponse,
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
    ) -> ContractResponse:
        """Deletes the Contract with the specified UUID.

        Used to remove an existing
        Contract from an Account.

        **Note:** This call will fail if there are any AccountPlans or Commitments that
        have been added to the Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    def end_date_billing_entities(
        self,
        id: str,
        *,
        org_id: str | None = None,
        billing_entities: List[Literal["CONTRACT", "ACCOUNTPLAN", "PREPAYMENT", "PRICINGS", "COUNTER_PRICINGS"]],
        end_date: Union[str, datetime],
        apply_to_children: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractEndDateBillingEntitiesResponse:
        """
        Apply the specified end-date to billing entities associated with Accounts the
        Contract has been added to, and apply the end-date to the Contract itself.

        **NOTES:**

        - If you want to apply the end-date to the Contract _itself_ - the Contract `id`
          you use as the required PATH PARAMETER - you must also specify `CONTRACT` as a
          `billingEntities` option in the request body schema.
        - Only the Contract whose id you specify for the PATH PARAMETER will be
          end-dated. If there are other Contracts associated with the Account, these
          will not be end-dated.
        - When you successfully end-date billing entities, the version number of each
          entity is incremented.

        Args:
          billing_entities: Defines which billing entities associated with the Account will have the
              specified end-date applied. For example, if you want the specified end-date to
              be applied to all Prepayments/Commitments created for the Account use
              `"PREPAYMENT"`.

          end_date: The end date and time applied to the specified billing entities _(in ISO 8601
              format)_.

          apply_to_children: A Boolean TRUE/FALSE flag. For Parent Accounts, set to TRUE if you want the
              specified end-date to be applied to any billing entities associated with Child
              Accounts. _(Optional)_

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
            f"/organizations/{org_id}/contracts/{id}/enddatebillingentities",
            body=maybe_transform(
                {
                    "billing_entities": billing_entities,
                    "end_date": end_date,
                    "apply_to_children": apply_to_children,
                },
                contract_end_date_billing_entities_params.ContractEndDateBillingEntitiesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractEndDateBillingEntitiesResponse,
        )


class AsyncContractsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncContractsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncContractsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncContractsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncContractsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        account_id: str,
        end_date: Union[str, date],
        name: str,
        start_date: Union[str, date],
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractResponse:
        """Create a new Contract.

        Creates a new Contract for the specified Account.

        The Contract includes
        information such as the associated Account along with start and end dates.

        Args:
          account_id: The unique identifier (UUID) of the Account associated with this Contract.

          end_date: The exclusive end date of the Contract _(in ISO-8601 format)_. This means the
              Contract is active until midnight on the day **_before_** this date.

          name: The name of the Contract.

          start_date: The start date for the Contract _(in ISO-8601 format)_. This date is inclusive,
              meaning the Contract is active from this date onward.

          code: The short code of the Contract.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: The description of the Contract, which provides context and information.

          purchase_order_number: The Purchase Order Number associated with the Contract.

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
            f"/organizations/{org_id}/contracts",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "end_date": end_date,
                    "name": name,
                    "start_date": start_date,
                    "code": code,
                    "custom_fields": custom_fields,
                    "description": description,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                contract_create_params.ContractCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
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
    ) -> ContractResponse:
        """Retrieves the Contract with the given UUID.

        Used to obtain the details of a
        Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        account_id: str,
        end_date: Union[str, date],
        name: str,
        start_date: Union[str, date],
        code: str | Omit = omit,
        custom_fields: Dict[str, Union[str, float]] | Omit = omit,
        description: str | Omit = omit,
        purchase_order_number: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractResponse:
        """
        Update the Contract with the given UUID.

        This endpoint updates the details of the Contract with the specified ID. Used to
        modify details of an existing Contract such as the start or end dates.

        **Note:** If you have created Custom Fields for a Contract, when you use this
        endpoint to update the Contract use the `customFields` parameter to preserve
        those Custom Fields. If you omit them from the update request, they will be
        lost.

        Args:
          account_id: The unique identifier (UUID) of the Account associated with this Contract.

          end_date: The exclusive end date of the Contract _(in ISO-8601 format)_. This means the
              Contract is active until midnight on the day **_before_** this date.

          name: The name of the Contract.

          start_date: The start date for the Contract _(in ISO-8601 format)_. This date is inclusive,
              meaning the Contract is active from this date onward.

          code: The short code of the Contract.

          custom_fields: User defined fields enabling you to attach custom data. The value for a custom
              field can be either a string or a number.

              If `customFields` can also be defined for this entity at the Organizational
              level, `customField` values defined at individual level override values of
              `customFields` with the same name defined at Organization level.

              See
              [Working with Custom Fields](https://www.m3ter.com/docs/guides/creating-and-managing-products/working-with-custom-fields)
              in the m3ter documentation for more information.

          description: The description of the Contract, which provides context and information.

          purchase_order_number: The Purchase Order Number associated with the Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            body=await async_maybe_transform(
                {
                    "account_id": account_id,
                    "end_date": end_date,
                    "name": name,
                    "start_date": start_date,
                    "code": code,
                    "custom_fields": custom_fields,
                    "description": description,
                    "purchase_order_number": purchase_order_number,
                    "version": version,
                },
                contract_update_params.ContractUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        account_id: Optional[str] | Omit = omit,
        codes: SequenceNotStr[str] | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ContractResponse, AsyncCursor[ContractResponse]]:
        """Retrieves a list of Contracts by Organization ID.

        Supports pagination and
        includes various query parameters to filter the Contracts returned based on
        Contract IDs or short codes.

        Args:
          codes: An optional parameter to retrieve specific Contracts based on their short codes.

          ids: An optional parameter to filter the list based on specific Contract unique
              identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Contracts in a paginated list.

          page_size: Specifies the maximum number of Contracts to retrieve per page.

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
            f"/organizations/{org_id}/contracts",
            page=AsyncCursor[ContractResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "account_id": account_id,
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    contract_list_params.ContractListParams,
                ),
            ),
            model=ContractResponse,
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
    ) -> ContractResponse:
        """Deletes the Contract with the specified UUID.

        Used to remove an existing
        Contract from an Account.

        **Note:** This call will fail if there are any AccountPlans or Commitments that
        have been added to the Contract.

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
            f"/organizations/{org_id}/contracts/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractResponse,
        )

    async def end_date_billing_entities(
        self,
        id: str,
        *,
        org_id: str | None = None,
        billing_entities: List[Literal["CONTRACT", "ACCOUNTPLAN", "PREPAYMENT", "PRICINGS", "COUNTER_PRICINGS"]],
        end_date: Union[str, datetime],
        apply_to_children: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ContractEndDateBillingEntitiesResponse:
        """
        Apply the specified end-date to billing entities associated with Accounts the
        Contract has been added to, and apply the end-date to the Contract itself.

        **NOTES:**

        - If you want to apply the end-date to the Contract _itself_ - the Contract `id`
          you use as the required PATH PARAMETER - you must also specify `CONTRACT` as a
          `billingEntities` option in the request body schema.
        - Only the Contract whose id you specify for the PATH PARAMETER will be
          end-dated. If there are other Contracts associated with the Account, these
          will not be end-dated.
        - When you successfully end-date billing entities, the version number of each
          entity is incremented.

        Args:
          billing_entities: Defines which billing entities associated with the Account will have the
              specified end-date applied. For example, if you want the specified end-date to
              be applied to all Prepayments/Commitments created for the Account use
              `"PREPAYMENT"`.

          end_date: The end date and time applied to the specified billing entities _(in ISO 8601
              format)_.

          apply_to_children: A Boolean TRUE/FALSE flag. For Parent Accounts, set to TRUE if you want the
              specified end-date to be applied to any billing entities associated with Child
              Accounts. _(Optional)_

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
            f"/organizations/{org_id}/contracts/{id}/enddatebillingentities",
            body=await async_maybe_transform(
                {
                    "billing_entities": billing_entities,
                    "end_date": end_date,
                    "apply_to_children": apply_to_children,
                },
                contract_end_date_billing_entities_params.ContractEndDateBillingEntitiesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ContractEndDateBillingEntitiesResponse,
        )


class ContractsResourceWithRawResponse:
    def __init__(self, contracts: ContractsResource) -> None:
        self._contracts = contracts

        self.create = to_raw_response_wrapper(
            contracts.create,
        )
        self.retrieve = to_raw_response_wrapper(
            contracts.retrieve,
        )
        self.update = to_raw_response_wrapper(
            contracts.update,
        )
        self.list = to_raw_response_wrapper(
            contracts.list,
        )
        self.delete = to_raw_response_wrapper(
            contracts.delete,
        )
        self.end_date_billing_entities = to_raw_response_wrapper(
            contracts.end_date_billing_entities,
        )


class AsyncContractsResourceWithRawResponse:
    def __init__(self, contracts: AsyncContractsResource) -> None:
        self._contracts = contracts

        self.create = async_to_raw_response_wrapper(
            contracts.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            contracts.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            contracts.update,
        )
        self.list = async_to_raw_response_wrapper(
            contracts.list,
        )
        self.delete = async_to_raw_response_wrapper(
            contracts.delete,
        )
        self.end_date_billing_entities = async_to_raw_response_wrapper(
            contracts.end_date_billing_entities,
        )


class ContractsResourceWithStreamingResponse:
    def __init__(self, contracts: ContractsResource) -> None:
        self._contracts = contracts

        self.create = to_streamed_response_wrapper(
            contracts.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            contracts.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            contracts.update,
        )
        self.list = to_streamed_response_wrapper(
            contracts.list,
        )
        self.delete = to_streamed_response_wrapper(
            contracts.delete,
        )
        self.end_date_billing_entities = to_streamed_response_wrapper(
            contracts.end_date_billing_entities,
        )


class AsyncContractsResourceWithStreamingResponse:
    def __init__(self, contracts: AsyncContractsResource) -> None:
        self._contracts = contracts

        self.create = async_to_streamed_response_wrapper(
            contracts.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            contracts.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            contracts.update,
        )
        self.list = async_to_streamed_response_wrapper(
            contracts.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            contracts.delete,
        )
        self.end_date_billing_entities = async_to_streamed_response_wrapper(
            contracts.end_date_billing_entities,
        )
