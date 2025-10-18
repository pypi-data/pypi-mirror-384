# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import plan_group_link_list_params, plan_group_link_create_params, plan_group_link_update_params
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
from ..types.plan_group_link_response import PlanGroupLinkResponse

__all__ = ["PlanGroupLinksResource", "AsyncPlanGroupLinksResource"]


class PlanGroupLinksResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PlanGroupLinksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PlanGroupLinksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PlanGroupLinksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PlanGroupLinksResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        plan_group_id: str,
        plan_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupLinkResponse:
        """
        Create a new PlanGroupLink.

        Args:
          plan_group_id

          plan_id

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
            f"/organizations/{org_id}/plangrouplinks",
            body=maybe_transform(
                {
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                plan_group_link_create_params.PlanGroupLinkCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
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
    ) -> PlanGroupLinkResponse:
        """
        Retrieve a PlanGroupLink for the given UUID.

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        plan_group_id: str,
        plan_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupLinkResponse:
        """
        Update PlanGroupLink for the given UUID.

        Args:
          plan_group_id

          plan_id

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            body=maybe_transform(
                {
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                plan_group_link_update_params.PlanGroupLinkUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan: str | Omit = omit,
        plan_group: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[PlanGroupLinkResponse]:
        """
        Retrieve a list of PlanGroupLink entities

        Args:
          ids: list of IDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of PlanGroupLinks to retrieve per page

          plan: UUID of the Plan to retrieve PlanGroupLinks for

          plan_group: UUID of the PlanGroup to retrieve PlanGroupLinks for

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
            f"/organizations/{org_id}/plangrouplinks",
            page=SyncCursor[PlanGroupLinkResponse],
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
                        "plan": plan,
                        "plan_group": plan_group,
                    },
                    plan_group_link_list_params.PlanGroupLinkListParams,
                ),
            ),
            model=PlanGroupLinkResponse,
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
    ) -> PlanGroupLinkResponse:
        """
        Delete a PlanGroupLink for the given UUID.

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )


class AsyncPlanGroupLinksResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPlanGroupLinksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPlanGroupLinksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPlanGroupLinksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPlanGroupLinksResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        plan_group_id: str,
        plan_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupLinkResponse:
        """
        Create a new PlanGroupLink.

        Args:
          plan_group_id

          plan_id

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
            f"/organizations/{org_id}/plangrouplinks",
            body=await async_maybe_transform(
                {
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                plan_group_link_create_params.PlanGroupLinkCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
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
    ) -> PlanGroupLinkResponse:
        """
        Retrieve a PlanGroupLink for the given UUID.

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        plan_group_id: str,
        plan_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PlanGroupLinkResponse:
        """
        Update PlanGroupLink for the given UUID.

        Args:
          plan_group_id

          plan_id

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            body=await async_maybe_transform(
                {
                    "plan_group_id": plan_group_id,
                    "plan_id": plan_id,
                    "version": version,
                },
                plan_group_link_update_params.PlanGroupLinkUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        plan: str | Omit = omit,
        plan_group: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[PlanGroupLinkResponse, AsyncCursor[PlanGroupLinkResponse]]:
        """
        Retrieve a list of PlanGroupLink entities

        Args:
          ids: list of IDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of PlanGroupLinks to retrieve per page

          plan: UUID of the Plan to retrieve PlanGroupLinks for

          plan_group: UUID of the PlanGroup to retrieve PlanGroupLinks for

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
            f"/organizations/{org_id}/plangrouplinks",
            page=AsyncCursor[PlanGroupLinkResponse],
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
                        "plan": plan,
                        "plan_group": plan_group,
                    },
                    plan_group_link_list_params.PlanGroupLinkListParams,
                ),
            ),
            model=PlanGroupLinkResponse,
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
    ) -> PlanGroupLinkResponse:
        """
        Delete a PlanGroupLink for the given UUID.

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
            f"/organizations/{org_id}/plangrouplinks/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PlanGroupLinkResponse,
        )


class PlanGroupLinksResourceWithRawResponse:
    def __init__(self, plan_group_links: PlanGroupLinksResource) -> None:
        self._plan_group_links = plan_group_links

        self.create = to_raw_response_wrapper(
            plan_group_links.create,
        )
        self.retrieve = to_raw_response_wrapper(
            plan_group_links.retrieve,
        )
        self.update = to_raw_response_wrapper(
            plan_group_links.update,
        )
        self.list = to_raw_response_wrapper(
            plan_group_links.list,
        )
        self.delete = to_raw_response_wrapper(
            plan_group_links.delete,
        )


class AsyncPlanGroupLinksResourceWithRawResponse:
    def __init__(self, plan_group_links: AsyncPlanGroupLinksResource) -> None:
        self._plan_group_links = plan_group_links

        self.create = async_to_raw_response_wrapper(
            plan_group_links.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            plan_group_links.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            plan_group_links.update,
        )
        self.list = async_to_raw_response_wrapper(
            plan_group_links.list,
        )
        self.delete = async_to_raw_response_wrapper(
            plan_group_links.delete,
        )


class PlanGroupLinksResourceWithStreamingResponse:
    def __init__(self, plan_group_links: PlanGroupLinksResource) -> None:
        self._plan_group_links = plan_group_links

        self.create = to_streamed_response_wrapper(
            plan_group_links.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            plan_group_links.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            plan_group_links.update,
        )
        self.list = to_streamed_response_wrapper(
            plan_group_links.list,
        )
        self.delete = to_streamed_response_wrapper(
            plan_group_links.delete,
        )


class AsyncPlanGroupLinksResourceWithStreamingResponse:
    def __init__(self, plan_group_links: AsyncPlanGroupLinksResource) -> None:
        self._plan_group_links = plan_group_links

        self.create = async_to_streamed_response_wrapper(
            plan_group_links.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            plan_group_links.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            plan_group_links.update,
        )
        self.list = async_to_streamed_response_wrapper(
            plan_group_links.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            plan_group_links.delete,
        )
