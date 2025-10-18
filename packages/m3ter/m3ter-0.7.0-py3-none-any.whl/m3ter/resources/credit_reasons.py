# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import credit_reason_list_params, credit_reason_create_params, credit_reason_update_params
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
from ..types.credit_reason_response import CreditReasonResponse

__all__ = ["CreditReasonsResource", "AsyncCreditReasonsResource"]


class CreditReasonsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CreditReasonsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CreditReasonsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CreditReasonsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CreditReasonsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreditReasonResponse:
        """Create a new Credit Reason for your Organization.

        When you've created a Credit
        Reason, it becomes available as a credit type for adding Credit line items to
        Bills. See [Credits](https://www.m3ter.com/docs/api#tag/Credits).

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

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
            f"/organizations/{org_id}/picklists/creditreasons",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                credit_reason_create_params.CreditReasonCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
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
    ) -> CreditReasonResponse:
        """
        Retrieve the Credit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreditReasonResponse:
        """
        Update the Credit Reason with the given UUID.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                credit_reason_update_params.CreditReasonUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        archived: bool | Omit = omit,
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
    ) -> SyncCursor[CreditReasonResponse]:
        """Retrieve a list of the Credit Reason entities created for your Organization.

        You
        can filter the list returned for the call by Credit Reason ID, Credit Reason
        short code, or by Archive status.

        Args:
          archived: TRUE / FALSE archived flag to filter the list. CreditReasons can be archived
              once they are obsolete.

              - TRUE includes archived CreditReasons.
              - FALSE excludes CreditReasons that are archived.

          codes: List of Credit Reason short codes to retrieve.

          ids: List of Credit Reason IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of credit reasons to retrieve per page.

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
            f"/organizations/{org_id}/picklists/creditreasons",
            page=SyncCursor[CreditReasonResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "archived": archived,
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    credit_reason_list_params.CreditReasonListParams,
                ),
            ),
            model=CreditReasonResponse,
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
    ) -> CreditReasonResponse:
        """
        Delete the Credit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )


class AsyncCreditReasonsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCreditReasonsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCreditReasonsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCreditReasonsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCreditReasonsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreditReasonResponse:
        """Create a new Credit Reason for your Organization.

        When you've created a Credit
        Reason, it becomes available as a credit type for adding Credit line items to
        Bills. See [Credits](https://www.m3ter.com/docs/api#tag/Credits).

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

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
            f"/organizations/{org_id}/picklists/creditreasons",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                credit_reason_create_params.CreditReasonCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
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
    ) -> CreditReasonResponse:
        """
        Retrieve the Credit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreditReasonResponse:
        """
        Update the Credit Reason with the given UUID.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                credit_reason_update_params.CreditReasonUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        archived: bool | Omit = omit,
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
    ) -> AsyncPaginator[CreditReasonResponse, AsyncCursor[CreditReasonResponse]]:
        """Retrieve a list of the Credit Reason entities created for your Organization.

        You
        can filter the list returned for the call by Credit Reason ID, Credit Reason
        short code, or by Archive status.

        Args:
          archived: TRUE / FALSE archived flag to filter the list. CreditReasons can be archived
              once they are obsolete.

              - TRUE includes archived CreditReasons.
              - FALSE excludes CreditReasons that are archived.

          codes: List of Credit Reason short codes to retrieve.

          ids: List of Credit Reason IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of credit reasons to retrieve per page.

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
            f"/organizations/{org_id}/picklists/creditreasons",
            page=AsyncCursor[CreditReasonResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "archived": archived,
                        "codes": codes,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    credit_reason_list_params.CreditReasonListParams,
                ),
            ),
            model=CreditReasonResponse,
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
    ) -> CreditReasonResponse:
        """
        Delete the Credit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/creditreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreditReasonResponse,
        )


class CreditReasonsResourceWithRawResponse:
    def __init__(self, credit_reasons: CreditReasonsResource) -> None:
        self._credit_reasons = credit_reasons

        self.create = to_raw_response_wrapper(
            credit_reasons.create,
        )
        self.retrieve = to_raw_response_wrapper(
            credit_reasons.retrieve,
        )
        self.update = to_raw_response_wrapper(
            credit_reasons.update,
        )
        self.list = to_raw_response_wrapper(
            credit_reasons.list,
        )
        self.delete = to_raw_response_wrapper(
            credit_reasons.delete,
        )


class AsyncCreditReasonsResourceWithRawResponse:
    def __init__(self, credit_reasons: AsyncCreditReasonsResource) -> None:
        self._credit_reasons = credit_reasons

        self.create = async_to_raw_response_wrapper(
            credit_reasons.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            credit_reasons.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            credit_reasons.update,
        )
        self.list = async_to_raw_response_wrapper(
            credit_reasons.list,
        )
        self.delete = async_to_raw_response_wrapper(
            credit_reasons.delete,
        )


class CreditReasonsResourceWithStreamingResponse:
    def __init__(self, credit_reasons: CreditReasonsResource) -> None:
        self._credit_reasons = credit_reasons

        self.create = to_streamed_response_wrapper(
            credit_reasons.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            credit_reasons.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            credit_reasons.update,
        )
        self.list = to_streamed_response_wrapper(
            credit_reasons.list,
        )
        self.delete = to_streamed_response_wrapper(
            credit_reasons.delete,
        )


class AsyncCreditReasonsResourceWithStreamingResponse:
    def __init__(self, credit_reasons: AsyncCreditReasonsResource) -> None:
        self._credit_reasons = credit_reasons

        self.create = async_to_streamed_response_wrapper(
            credit_reasons.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            credit_reasons.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            credit_reasons.update,
        )
        self.list = async_to_streamed_response_wrapper(
            credit_reasons.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            credit_reasons.delete,
        )
