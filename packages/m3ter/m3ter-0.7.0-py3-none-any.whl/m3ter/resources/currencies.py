# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import currency_list_params, currency_create_params, currency_update_params
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
from ..types.currency_response import CurrencyResponse

__all__ = ["CurrenciesResource", "AsyncCurrenciesResource"]


class CurrenciesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CurrenciesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return CurrenciesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CurrenciesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return CurrenciesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        max_decimal_places: int | Omit = omit,
        rounding_mode: Literal["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]
        | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrencyResponse:
        """
        Creates a new Currency for the specified Organization.

        Used to create a Currency that your Organization will start to use.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

          max_decimal_places: Indicates the maximum number of decimal places to use for this Currency.

          rounding_mode

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
            f"/organizations/{org_id}/picklists/currency",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "max_decimal_places": max_decimal_places,
                    "rounding_mode": rounding_mode,
                    "version": version,
                },
                currency_create_params.CurrencyCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
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
    ) -> CurrencyResponse:
        """Retrieve the specified Currency with the given UUID.

        Used to obtain the details
        of a specified existing Currency in your Organization.

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        max_decimal_places: int | Omit = omit,
        rounding_mode: Literal["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]
        | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrencyResponse:
        """
        Update a Currency with the given UUID.

        Used to update the attributes of the specified Currency for the specified
        Organization.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

          max_decimal_places: Indicates the maximum number of decimal places to use for this Currency.

          rounding_mode

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "max_decimal_places": max_decimal_places,
                    "rounding_mode": rounding_mode,
                    "version": version,
                },
                currency_update_params.CurrencyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
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
    ) -> SyncCursor[CurrencyResponse]:
        """
        Retrieve a list of Currencies.

        Retrieves a list of Currencies for the specified Organization. This endpoint
        supports pagination and includes various query parameters to filter the
        Currencies based on Currency ID, and short codes.

        Args:
          archived: Filter by archived flag. A True / False flag indicating whether to return
              Currencies that are archived _(obsolete)_.

              - TRUE - return archived Currencies.
              - FALSE - archived Currencies are not returned.

          codes: An optional parameter to retrieve specific Currencies based on their short
              codes.

          ids: An optional parameter to filter the list based on specific Currency unique
              identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Currencies in a paginated list.

          page_size: Specifies the maximum number of Currencies to retrieve per page.

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
            f"/organizations/{org_id}/picklists/currency",
            page=SyncCursor[CurrencyResponse],
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
                    currency_list_params.CurrencyListParams,
                ),
            ),
            model=CurrencyResponse,
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
    ) -> CurrencyResponse:
        """
        Delete the Currency with the given UUID.

        Used to remove an existing Currency from your Organization that is no longer
        required.

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
        )


class AsyncCurrenciesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCurrenciesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCurrenciesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCurrenciesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncCurrenciesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        max_decimal_places: int | Omit = omit,
        rounding_mode: Literal["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]
        | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrencyResponse:
        """
        Creates a new Currency for the specified Organization.

        Used to create a Currency that your Organization will start to use.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

          max_decimal_places: Indicates the maximum number of decimal places to use for this Currency.

          rounding_mode

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
            f"/organizations/{org_id}/picklists/currency",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "max_decimal_places": max_decimal_places,
                    "rounding_mode": rounding_mode,
                    "version": version,
                },
                currency_create_params.CurrencyCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
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
    ) -> CurrencyResponse:
        """Retrieve the specified Currency with the given UUID.

        Used to obtain the details
        of a specified existing Currency in your Organization.

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        archived: bool | Omit = omit,
        code: str | Omit = omit,
        max_decimal_places: int | Omit = omit,
        rounding_mode: Literal["UP", "DOWN", "CEILING", "FLOOR", "HALF_UP", "HALF_DOWN", "HALF_EVEN", "UNNECESSARY"]
        | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CurrencyResponse:
        """
        Update a Currency with the given UUID.

        Used to update the attributes of the specified Currency for the specified
        Organization.

        Args:
          name: The name of the entity.

          archived: A Boolean TRUE / FALSE flag indicating whether the entity is archived. An entity
              can be archived if it is obsolete.

              - TRUE - the entity is in the archived state.
              - FALSE - the entity is not in the archived state.

          code: The short code for the entity.

          max_decimal_places: Indicates the maximum number of decimal places to use for this Currency.

          rounding_mode

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "archived": archived,
                    "code": code,
                    "max_decimal_places": max_decimal_places,
                    "rounding_mode": rounding_mode,
                    "version": version,
                },
                currency_update_params.CurrencyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
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
    ) -> AsyncPaginator[CurrencyResponse, AsyncCursor[CurrencyResponse]]:
        """
        Retrieve a list of Currencies.

        Retrieves a list of Currencies for the specified Organization. This endpoint
        supports pagination and includes various query parameters to filter the
        Currencies based on Currency ID, and short codes.

        Args:
          archived: Filter by archived flag. A True / False flag indicating whether to return
              Currencies that are archived _(obsolete)_.

              - TRUE - return archived Currencies.
              - FALSE - archived Currencies are not returned.

          codes: An optional parameter to retrieve specific Currencies based on their short
              codes.

          ids: An optional parameter to filter the list based on specific Currency unique
              identifiers (UUIDs).

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Currencies in a paginated list.

          page_size: Specifies the maximum number of Currencies to retrieve per page.

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
            f"/organizations/{org_id}/picklists/currency",
            page=AsyncCursor[CurrencyResponse],
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
                    currency_list_params.CurrencyListParams,
                ),
            ),
            model=CurrencyResponse,
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
    ) -> CurrencyResponse:
        """
        Delete the Currency with the given UUID.

        Used to remove an existing Currency from your Organization that is no longer
        required.

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
            f"/organizations/{org_id}/picklists/currency/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CurrencyResponse,
        )


class CurrenciesResourceWithRawResponse:
    def __init__(self, currencies: CurrenciesResource) -> None:
        self._currencies = currencies

        self.create = to_raw_response_wrapper(
            currencies.create,
        )
        self.retrieve = to_raw_response_wrapper(
            currencies.retrieve,
        )
        self.update = to_raw_response_wrapper(
            currencies.update,
        )
        self.list = to_raw_response_wrapper(
            currencies.list,
        )
        self.delete = to_raw_response_wrapper(
            currencies.delete,
        )


class AsyncCurrenciesResourceWithRawResponse:
    def __init__(self, currencies: AsyncCurrenciesResource) -> None:
        self._currencies = currencies

        self.create = async_to_raw_response_wrapper(
            currencies.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            currencies.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            currencies.update,
        )
        self.list = async_to_raw_response_wrapper(
            currencies.list,
        )
        self.delete = async_to_raw_response_wrapper(
            currencies.delete,
        )


class CurrenciesResourceWithStreamingResponse:
    def __init__(self, currencies: CurrenciesResource) -> None:
        self._currencies = currencies

        self.create = to_streamed_response_wrapper(
            currencies.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            currencies.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            currencies.update,
        )
        self.list = to_streamed_response_wrapper(
            currencies.list,
        )
        self.delete = to_streamed_response_wrapper(
            currencies.delete,
        )


class AsyncCurrenciesResourceWithStreamingResponse:
    def __init__(self, currencies: AsyncCurrenciesResource) -> None:
        self._currencies = currencies

        self.create = async_to_streamed_response_wrapper(
            currencies.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            currencies.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            currencies.update,
        )
        self.list = async_to_streamed_response_wrapper(
            currencies.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            currencies.delete,
        )
