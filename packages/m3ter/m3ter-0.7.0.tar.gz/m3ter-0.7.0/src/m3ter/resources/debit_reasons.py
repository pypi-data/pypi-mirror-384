# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import debit_reason_list_params, debit_reason_create_params, debit_reason_update_params
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
from ..types.debit_reason_response import DebitReasonResponse

__all__ = ["DebitReasonsResource", "AsyncDebitReasonsResource"]


class DebitReasonsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DebitReasonsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return DebitReasonsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DebitReasonsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return DebitReasonsResourceWithStreamingResponse(self)

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
    ) -> DebitReasonResponse:
        """Create a new Debit Reason for your Organization.

        When you've created a Debit
        Reason, it becomes available as a debit type for adding Debit line items to
        Bills. See [Debits](https://www.m3ter.com/docs/api#tag/Debits).

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
            f"/organizations/{org_id}/picklists/debitreasons",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                debit_reason_create_params.DebitReasonCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Retrieve the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Update the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                debit_reason_update_params.DebitReasonUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> SyncCursor[DebitReasonResponse]:
        """Retrieve a list of the Debit Reason entities created for your Organization.

        You
        can filter the list returned for the call by Debit Reason ID, Debit Reason short
        code, or by Archive status.

        Args:
          archived: Filter using the boolean archived flag. DebitReasons can be archived if they are
              obsolete.

              - TRUE includes DebitReasons that have been archived.
              - FALSE excludes archived DebitReasons.

          codes: List of Debit Reason short codes to retrieve.

          ids: List of Debit Reason IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of Debit Reasons to retrieve per page.

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
            f"/organizations/{org_id}/picklists/debitreasons",
            page=SyncCursor[DebitReasonResponse],
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
                    debit_reason_list_params.DebitReasonListParams,
                ),
            ),
            model=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Delete the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
        )


class AsyncDebitReasonsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDebitReasonsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDebitReasonsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDebitReasonsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncDebitReasonsResourceWithStreamingResponse(self)

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
    ) -> DebitReasonResponse:
        """Create a new Debit Reason for your Organization.

        When you've created a Debit
        Reason, it becomes available as a debit type for adding Debit line items to
        Bills. See [Debits](https://www.m3ter.com/docs/api#tag/Debits).

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
            f"/organizations/{org_id}/picklists/debitreasons",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                debit_reason_create_params.DebitReasonCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Retrieve the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Update the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "version": version,
                },
                debit_reason_update_params.DebitReasonUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
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
    ) -> AsyncPaginator[DebitReasonResponse, AsyncCursor[DebitReasonResponse]]:
        """Retrieve a list of the Debit Reason entities created for your Organization.

        You
        can filter the list returned for the call by Debit Reason ID, Debit Reason short
        code, or by Archive status.

        Args:
          archived: Filter using the boolean archived flag. DebitReasons can be archived if they are
              obsolete.

              - TRUE includes DebitReasons that have been archived.
              - FALSE excludes archived DebitReasons.

          codes: List of Debit Reason short codes to retrieve.

          ids: List of Debit Reason IDs to retrieve.

          next_token: `nextToken` for multi page retrievals.

          page_size: Number of Debit Reasons to retrieve per page.

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
            f"/organizations/{org_id}/picklists/debitreasons",
            page=AsyncCursor[DebitReasonResponse],
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
                    debit_reason_list_params.DebitReasonListParams,
                ),
            ),
            model=DebitReasonResponse,
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
    ) -> DebitReasonResponse:
        """
        Delete the Debit Reason with the given UUID.

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
            f"/organizations/{org_id}/picklists/debitreasons/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DebitReasonResponse,
        )


class DebitReasonsResourceWithRawResponse:
    def __init__(self, debit_reasons: DebitReasonsResource) -> None:
        self._debit_reasons = debit_reasons

        self.create = to_raw_response_wrapper(
            debit_reasons.create,
        )
        self.retrieve = to_raw_response_wrapper(
            debit_reasons.retrieve,
        )
        self.update = to_raw_response_wrapper(
            debit_reasons.update,
        )
        self.list = to_raw_response_wrapper(
            debit_reasons.list,
        )
        self.delete = to_raw_response_wrapper(
            debit_reasons.delete,
        )


class AsyncDebitReasonsResourceWithRawResponse:
    def __init__(self, debit_reasons: AsyncDebitReasonsResource) -> None:
        self._debit_reasons = debit_reasons

        self.create = async_to_raw_response_wrapper(
            debit_reasons.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            debit_reasons.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            debit_reasons.update,
        )
        self.list = async_to_raw_response_wrapper(
            debit_reasons.list,
        )
        self.delete = async_to_raw_response_wrapper(
            debit_reasons.delete,
        )


class DebitReasonsResourceWithStreamingResponse:
    def __init__(self, debit_reasons: DebitReasonsResource) -> None:
        self._debit_reasons = debit_reasons

        self.create = to_streamed_response_wrapper(
            debit_reasons.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            debit_reasons.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            debit_reasons.update,
        )
        self.list = to_streamed_response_wrapper(
            debit_reasons.list,
        )
        self.delete = to_streamed_response_wrapper(
            debit_reasons.delete,
        )


class AsyncDebitReasonsResourceWithStreamingResponse:
    def __init__(self, debit_reasons: AsyncDebitReasonsResource) -> None:
        self._debit_reasons = debit_reasons

        self.create = async_to_streamed_response_wrapper(
            debit_reasons.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            debit_reasons.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            debit_reasons.update,
        )
        self.list = async_to_streamed_response_wrapper(
            debit_reasons.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            debit_reasons.delete,
        )
