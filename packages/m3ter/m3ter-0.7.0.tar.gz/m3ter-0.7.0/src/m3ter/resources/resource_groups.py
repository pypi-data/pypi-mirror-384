# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import (
    resource_group_list_params,
    resource_group_create_params,
    resource_group_update_params,
    resource_group_add_resource_params,
    resource_group_list_contents_params,
    resource_group_remove_resource_params,
    resource_group_list_permissions_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..types.resource_group_response import ResourceGroupResponse
from ..types.permission_policy_response import PermissionPolicyResponse
from ..types.resource_group_list_contents_response import ResourceGroupListContentsResponse

__all__ = ["ResourceGroupsResource", "AsyncResourceGroupsResource"]


class ResourceGroupsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ResourceGroupsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ResourceGroupsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResourceGroupsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ResourceGroupsResourceWithStreamingResponse(self)

    def create(
        self,
        type: str,
        *,
        org_id: str | None = None,
        name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Create a ResourceGroup for the UUID

        Args:
          name

          version

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        return self._post(
            f"/organizations/{org_id}/resourcegroups/{type}",
            body=maybe_transform(
                {
                    "name": name,
                    "version": version,
                },
                resource_group_create_params.ResourceGroupCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Retrieve the ResourceGroup for the UUID

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
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Update the ResourceGroup for the UUID

        Args:
          name

          version

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._put(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "version": version,
                },
                resource_group_update_params.ResourceGroupUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def list(
        self,
        type: str,
        *,
        org_id: str | None = None,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ResourceGroupResponse]:
        """
        Retrieve a list of ResourceGroup entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of ResourceGroups to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}",
            page=SyncCursor[ResourceGroupResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_params.ResourceGroupListParams,
                ),
            ),
            model=ResourceGroupResponse,
        )

    def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Delete a ResourceGroup for the UUID

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
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._delete(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def add_resource(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        target_id: str,
        target_type: Literal["ITEM", "GROUP"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Add an item to a ResourceGroup.

        Args:
          target_id:
              The id of the item or group you want to:

              - _Add Item_ call: add to a Resource Group.
              - _Remove Item_ call: remove from the Resource Group.

          target_type: When adding to or removing from a Resource Group, specify whether a single item
              or group:

              - `item`
                - _Add Item_ call: use to add a single meter to a Resource Group
                - _Remove Item_ call: use to remove a single from a Resource Group.
              - `group`
                - _Add Item_ call: use to add a Resource Group to another Resource Group and
                  form a nested Resource Group
                - _Remove Item_ call: use remove a nested Resource Group from a Resource
                  Group.

          version: The version number of the group.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._post(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/addresource",
            body=maybe_transform(
                {
                    "target_id": target_id,
                    "target_type": target_type,
                    "version": version,
                },
                resource_group_add_resource_params.ResourceGroupAddResourceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def list_contents(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ResourceGroupListContentsResponse]:
        """
        Retrieve a list of items for a ResourceGroup

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of ResourceGroupItems to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/contents",
            page=SyncCursor[ResourceGroupListContentsResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_contents_params.ResourceGroupListContentsParams,
                ),
            ),
            model=ResourceGroupListContentsResponse,
            method="post",
        )

    def list_permissions(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[PermissionPolicyResponse]:
        """
        Retrieve a list of permission policies for a ResourceGroup

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of PermissionPolicy entities to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/permissions",
            page=SyncCursor[PermissionPolicyResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_permissions_params.ResourceGroupListPermissionsParams,
                ),
            ),
            model=PermissionPolicyResponse,
        )

    def remove_resource(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        target_id: str,
        target_type: Literal["ITEM", "GROUP"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Remove an item from a ResourceGroup.

        Args:
          target_id:
              The id of the item or group you want to:

              - _Add Item_ call: add to a Resource Group.
              - _Remove Item_ call: remove from the Resource Group.

          target_type: When adding to or removing from a Resource Group, specify whether a single item
              or group:

              - `item`
                - _Add Item_ call: use to add a single meter to a Resource Group
                - _Remove Item_ call: use to remove a single from a Resource Group.
              - `group`
                - _Add Item_ call: use to add a Resource Group to another Resource Group and
                  form a nested Resource Group
                - _Remove Item_ call: use remove a nested Resource Group from a Resource
                  Group.

          version: The version number of the group.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._post(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/removeresource",
            body=maybe_transform(
                {
                    "target_id": target_id,
                    "target_type": target_type,
                    "version": version,
                },
                resource_group_remove_resource_params.ResourceGroupRemoveResourceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )


class AsyncResourceGroupsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncResourceGroupsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncResourceGroupsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResourceGroupsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncResourceGroupsResourceWithStreamingResponse(self)

    async def create(
        self,
        type: str,
        *,
        org_id: str | None = None,
        name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Create a ResourceGroup for the UUID

        Args:
          name

          version

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        return await self._post(
            f"/organizations/{org_id}/resourcegroups/{type}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "version": version,
                },
                resource_group_create_params.ResourceGroupCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    async def retrieve(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Retrieve the ResourceGroup for the UUID

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
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        name: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Update the ResourceGroup for the UUID

        Args:
          name

          version

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._put(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "version": version,
                },
                resource_group_update_params.ResourceGroupUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def list(
        self,
        type: str,
        *,
        org_id: str | None = None,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ResourceGroupResponse, AsyncCursor[ResourceGroupResponse]]:
        """
        Retrieve a list of ResourceGroup entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of ResourceGroups to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}",
            page=AsyncCursor[ResourceGroupResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_params.ResourceGroupListParams,
                ),
            ),
            model=ResourceGroupResponse,
        )

    async def delete(
        self,
        id: str,
        *,
        org_id: str | None = None,
        type: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Delete a ResourceGroup for the UUID

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
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._delete(
            f"/organizations/{org_id}/resourcegroups/{type}/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    async def add_resource(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        target_id: str,
        target_type: Literal["ITEM", "GROUP"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Add an item to a ResourceGroup.

        Args:
          target_id:
              The id of the item or group you want to:

              - _Add Item_ call: add to a Resource Group.
              - _Remove Item_ call: remove from the Resource Group.

          target_type: When adding to or removing from a Resource Group, specify whether a single item
              or group:

              - `item`
                - _Add Item_ call: use to add a single meter to a Resource Group
                - _Remove Item_ call: use to remove a single from a Resource Group.
              - `group`
                - _Add Item_ call: use to add a Resource Group to another Resource Group and
                  form a nested Resource Group
                - _Remove Item_ call: use remove a nested Resource Group from a Resource
                  Group.

          version: The version number of the group.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return await self._post(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/addresource",
            body=await async_maybe_transform(
                {
                    "target_id": target_id,
                    "target_type": target_type,
                    "version": version,
                },
                resource_group_add_resource_params.ResourceGroupAddResourceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )

    def list_contents(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ResourceGroupListContentsResponse, AsyncCursor[ResourceGroupListContentsResponse]]:
        """
        Retrieve a list of items for a ResourceGroup

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of ResourceGroupItems to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/contents",
            page=AsyncCursor[ResourceGroupListContentsResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_contents_params.ResourceGroupListContentsParams,
                ),
            ),
            model=ResourceGroupListContentsResponse,
            method="post",
        )

    def list_permissions(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[PermissionPolicyResponse, AsyncCursor[PermissionPolicyResponse]]:
        """
        Retrieve a list of permission policies for a ResourceGroup

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of PermissionPolicy entities to retrieve per page

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/permissions",
            page=AsyncCursor[PermissionPolicyResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    resource_group_list_permissions_params.ResourceGroupListPermissionsParams,
                ),
            ),
            model=PermissionPolicyResponse,
        )

    async def remove_resource(
        self,
        resource_group_id: str,
        *,
        org_id: str | None = None,
        type: str,
        target_id: str,
        target_type: Literal["ITEM", "GROUP"],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResourceGroupResponse:
        """
        Remove an item from a ResourceGroup.

        Args:
          target_id:
              The id of the item or group you want to:

              - _Add Item_ call: add to a Resource Group.
              - _Remove Item_ call: remove from the Resource Group.

          target_type: When adding to or removing from a Resource Group, specify whether a single item
              or group:

              - `item`
                - _Add Item_ call: use to add a single meter to a Resource Group
                - _Remove Item_ call: use to remove a single from a Resource Group.
              - `group`
                - _Add Item_ call: use to add a Resource Group to another Resource Group and
                  form a nested Resource Group
                - _Remove Item_ call: use remove a nested Resource Group from a Resource
                  Group.

          version: The version number of the group.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not type:
            raise ValueError(f"Expected a non-empty value for `type` but received {type!r}")
        if not resource_group_id:
            raise ValueError(f"Expected a non-empty value for `resource_group_id` but received {resource_group_id!r}")
        return await self._post(
            f"/organizations/{org_id}/resourcegroups/{type}/{resource_group_id}/removeresource",
            body=await async_maybe_transform(
                {
                    "target_id": target_id,
                    "target_type": target_type,
                    "version": version,
                },
                resource_group_remove_resource_params.ResourceGroupRemoveResourceParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ResourceGroupResponse,
        )


class ResourceGroupsResourceWithRawResponse:
    def __init__(self, resource_groups: ResourceGroupsResource) -> None:
        self._resource_groups = resource_groups

        self.create = to_raw_response_wrapper(
            resource_groups.create,
        )
        self.retrieve = to_raw_response_wrapper(
            resource_groups.retrieve,
        )
        self.update = to_raw_response_wrapper(
            resource_groups.update,
        )
        self.list = to_raw_response_wrapper(
            resource_groups.list,
        )
        self.delete = to_raw_response_wrapper(
            resource_groups.delete,
        )
        self.add_resource = to_raw_response_wrapper(
            resource_groups.add_resource,
        )
        self.list_contents = to_raw_response_wrapper(
            resource_groups.list_contents,
        )
        self.list_permissions = to_raw_response_wrapper(
            resource_groups.list_permissions,
        )
        self.remove_resource = to_raw_response_wrapper(
            resource_groups.remove_resource,
        )


class AsyncResourceGroupsResourceWithRawResponse:
    def __init__(self, resource_groups: AsyncResourceGroupsResource) -> None:
        self._resource_groups = resource_groups

        self.create = async_to_raw_response_wrapper(
            resource_groups.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            resource_groups.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            resource_groups.update,
        )
        self.list = async_to_raw_response_wrapper(
            resource_groups.list,
        )
        self.delete = async_to_raw_response_wrapper(
            resource_groups.delete,
        )
        self.add_resource = async_to_raw_response_wrapper(
            resource_groups.add_resource,
        )
        self.list_contents = async_to_raw_response_wrapper(
            resource_groups.list_contents,
        )
        self.list_permissions = async_to_raw_response_wrapper(
            resource_groups.list_permissions,
        )
        self.remove_resource = async_to_raw_response_wrapper(
            resource_groups.remove_resource,
        )


class ResourceGroupsResourceWithStreamingResponse:
    def __init__(self, resource_groups: ResourceGroupsResource) -> None:
        self._resource_groups = resource_groups

        self.create = to_streamed_response_wrapper(
            resource_groups.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            resource_groups.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            resource_groups.update,
        )
        self.list = to_streamed_response_wrapper(
            resource_groups.list,
        )
        self.delete = to_streamed_response_wrapper(
            resource_groups.delete,
        )
        self.add_resource = to_streamed_response_wrapper(
            resource_groups.add_resource,
        )
        self.list_contents = to_streamed_response_wrapper(
            resource_groups.list_contents,
        )
        self.list_permissions = to_streamed_response_wrapper(
            resource_groups.list_permissions,
        )
        self.remove_resource = to_streamed_response_wrapper(
            resource_groups.remove_resource,
        )


class AsyncResourceGroupsResourceWithStreamingResponse:
    def __init__(self, resource_groups: AsyncResourceGroupsResource) -> None:
        self._resource_groups = resource_groups

        self.create = async_to_streamed_response_wrapper(
            resource_groups.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            resource_groups.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            resource_groups.update,
        )
        self.list = async_to_streamed_response_wrapper(
            resource_groups.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            resource_groups.delete,
        )
        self.add_resource = async_to_streamed_response_wrapper(
            resource_groups.add_resource,
        )
        self.list_contents = async_to_streamed_response_wrapper(
            resource_groups.list_contents,
        )
        self.list_permissions = async_to_streamed_response_wrapper(
            resource_groups.list_permissions,
        )
        self.remove_resource = async_to_streamed_response_wrapper(
            resource_groups.remove_resource,
        )
