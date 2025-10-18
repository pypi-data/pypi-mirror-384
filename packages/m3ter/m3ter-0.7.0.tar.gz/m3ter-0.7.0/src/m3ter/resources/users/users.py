# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import datetime

import httpx

from ...types import user_list_params, user_update_params, user_get_permissions_params, user_get_user_groups_params
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .invitations import (
    InvitationsResource,
    AsyncInvitationsResource,
    InvitationsResourceWithRawResponse,
    AsyncInvitationsResourceWithRawResponse,
    InvitationsResourceWithStreamingResponse,
    AsyncInvitationsResourceWithStreamingResponse,
)
from ...pagination import SyncCursor, AsyncCursor
from ..._base_client import AsyncPaginator, make_request_options
from ...types.user_response import UserResponse
from ...types.user_me_response import UserMeResponse
from ...types.resource_group_response import ResourceGroupResponse
from ...types.permission_policy_response import PermissionPolicyResponse
from ...types.permission_statement_response_param import PermissionStatementResponseParam

__all__ = ["UsersResource", "AsyncUsersResource"]


class UsersResource(SyncAPIResource):
    @cached_property
    def invitations(self) -> InvitationsResource:
        return InvitationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> UsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return UsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return UsersResourceWithStreamingResponse(self)

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
    ) -> UserResponse:
        """
        Retrieve the OrgUser with the given UUID.

        Retrieves detailed information for a specific user within an Organization, using
        their unique identifier (UUID).

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
            f"/organizations/{org_id}/users/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        dt_end_access: Union[str, datetime] | Omit = omit,
        permission_policy: Iterable[PermissionStatementResponseParam] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserResponse:
        """
        Update the OrgUser with the given UUID.

        Updates the details for a specific user within an Organization using their
        unique identifier (UUID). Use this endpoint when you need to modify user
        information such as their permission policy.

        Args:
          dt_end_access: The date and time _(in ISO 8601 format)_ when the user's access will end. Use
              this to set or update the expiration of the user's access.

          permission_policy: An array of permission statements for the user. Each permission statement
              defines a specific permission for the user.

              See
              [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions)
              for more information.

          version:
              The version number of the entity:

              - **Newly created entity:** On initial Create, version is set at 1 and listed in
                the response.
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
            f"/organizations/{org_id}/users/{id}",
            body=maybe_transform(
                {
                    "dt_end_access": dt_end_access,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                user_update_params.UserUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[UserResponse]:
        """
        Retrieve a list of OrgUsers.

        Retrieves a list of all users within a specified Organization. Use this endpoint
        to get an overview of all users and their basic details. The list can be
        paginated for easier management.

        Args:
          ids: list of ids to retrieve

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              OrgUsers in a paginated list.

          page_size: Specifies the maximum number of OrgUsers to retrieve per page.

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
            f"/organizations/{org_id}/users",
            page=SyncCursor[UserResponse],
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
                    },
                    user_list_params.UserListParams,
                ),
            ),
            model=UserResponse,
        )

    def get_permissions(
        self,
        id: str,
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
    ) -> PermissionPolicyResponse:
        """
        Retrieve the permissions for the OrgUser with the given UUID.

        Retrieves a list of all permissions associated with a specific user in an
        Organization using their UUID. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Permission Policies in a paginated list.

          page_size: Specifies the maximum number of Permission Policies to retrieve per page.

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
            f"/organizations/{org_id}/users/{id}/permissions",
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
                    user_get_permissions_params.UserGetPermissionsParams,
                ),
            ),
            cast_to=PermissionPolicyResponse,
        )

    def get_user_groups(
        self,
        id: str,
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
    ) -> ResourceGroupResponse:
        """
        Retrieve a list of User Groups for an OrgUser.

        Retrieves a list of all User Groups that a specific user belongs to within an
        Organization. The list can be paginated for easier management.

        **Notes:**

        - **User Groups as Resource Groups**. A User Group is a Resource Group - one
          used to group resources of type `user`. You can use the _Create ResourceGroup_
          call detailed in the
          [ResourceGroup](https://www.m3ter.com/docs/api#tag/ResourceGroup) section to
          create a User Resource Group, and then use the _Add Item_ and _Remove Item_
          calls to manage which Users belong to the User Resource Group.
        - **Using the `inherited` parameter for the Retrieve OrgUser Groups call**.
          Resource Groups can be nested, which means a User Resource Group can contain
          another User Resource Group as a member. You can use the `inherited` parameter
          with this _Retrieve OrgUser Groups_ call as a _QUERY PARAMETER_ to control
          which User Resource Groups are returned:

        * If the user specified belongs to a User Resource Group that is nested as part
          of another User Resource Group:
          - If `inherited = TRUE`, then any Groups the user belongs to AND any parent
            Groups those Groups belong to as nested Groups are returned.
          - If `inherited = FALSE`, then only those User Resource Groups to which the
            user belongs are returned.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              User Groups in a paginated list.

          page_size: Specifies the maximum number of User Groups to retrieve per page.

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
            f"/organizations/{org_id}/users/{id}/usergroups",
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
                    user_get_user_groups_params.UserGetUserGroupsParams,
                ),
            ),
            cast_to=ResourceGroupResponse,
        )

    def me(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserMeResponse:
        """
        Retrieve information about the current user

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
        return self._get(
            f"/organizations/{org_id}/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserMeResponse,
        )

    def resend_password(
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
    ) -> None:
        """
        Resend temporary password for user

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/organizations/{org_id}/users/{id}/password/resend",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncUsersResource(AsyncAPIResource):
    @cached_property
    def invitations(self) -> AsyncInvitationsResource:
        return AsyncInvitationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncUsersResourceWithStreamingResponse(self)

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
    ) -> UserResponse:
        """
        Retrieve the OrgUser with the given UUID.

        Retrieves detailed information for a specific user within an Organization, using
        their unique identifier (UUID).

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
            f"/organizations/{org_id}/users/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        dt_end_access: Union[str, datetime] | Omit = omit,
        permission_policy: Iterable[PermissionStatementResponseParam] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserResponse:
        """
        Update the OrgUser with the given UUID.

        Updates the details for a specific user within an Organization using their
        unique identifier (UUID). Use this endpoint when you need to modify user
        information such as their permission policy.

        Args:
          dt_end_access: The date and time _(in ISO 8601 format)_ when the user's access will end. Use
              this to set or update the expiration of the user's access.

          permission_policy: An array of permission statements for the user. Each permission statement
              defines a specific permission for the user.

              See
              [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions)
              for more information.

          version:
              The version number of the entity:

              - **Newly created entity:** On initial Create, version is set at 1 and listed in
                the response.
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
            f"/organizations/{org_id}/users/{id}",
            body=await async_maybe_transform(
                {
                    "dt_end_access": dt_end_access,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                user_update_params.UserUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[UserResponse, AsyncCursor[UserResponse]]:
        """
        Retrieve a list of OrgUsers.

        Retrieves a list of all users within a specified Organization. Use this endpoint
        to get an overview of all users and their basic details. The list can be
        paginated for easier management.

        Args:
          ids: list of ids to retrieve

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              OrgUsers in a paginated list.

          page_size: Specifies the maximum number of OrgUsers to retrieve per page.

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
            f"/organizations/{org_id}/users",
            page=AsyncCursor[UserResponse],
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
                    },
                    user_list_params.UserListParams,
                ),
            ),
            model=UserResponse,
        )

    async def get_permissions(
        self,
        id: str,
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
    ) -> PermissionPolicyResponse:
        """
        Retrieve the permissions for the OrgUser with the given UUID.

        Retrieves a list of all permissions associated with a specific user in an
        Organization using their UUID. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Permission Policies in a paginated list.

          page_size: Specifies the maximum number of Permission Policies to retrieve per page.

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
            f"/organizations/{org_id}/users/{id}/permissions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    user_get_permissions_params.UserGetPermissionsParams,
                ),
            ),
            cast_to=PermissionPolicyResponse,
        )

    async def get_user_groups(
        self,
        id: str,
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
    ) -> ResourceGroupResponse:
        """
        Retrieve a list of User Groups for an OrgUser.

        Retrieves a list of all User Groups that a specific user belongs to within an
        Organization. The list can be paginated for easier management.

        **Notes:**

        - **User Groups as Resource Groups**. A User Group is a Resource Group - one
          used to group resources of type `user`. You can use the _Create ResourceGroup_
          call detailed in the
          [ResourceGroup](https://www.m3ter.com/docs/api#tag/ResourceGroup) section to
          create a User Resource Group, and then use the _Add Item_ and _Remove Item_
          calls to manage which Users belong to the User Resource Group.
        - **Using the `inherited` parameter for the Retrieve OrgUser Groups call**.
          Resource Groups can be nested, which means a User Resource Group can contain
          another User Resource Group as a member. You can use the `inherited` parameter
          with this _Retrieve OrgUser Groups_ call as a _QUERY PARAMETER_ to control
          which User Resource Groups are returned:

        * If the user specified belongs to a User Resource Group that is nested as part
          of another User Resource Group:
          - If `inherited = TRUE`, then any Groups the user belongs to AND any parent
            Groups those Groups belong to as nested Groups are returned.
          - If `inherited = FALSE`, then only those User Resource Groups to which the
            user belongs are returned.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              User Groups in a paginated list.

          page_size: Specifies the maximum number of User Groups to retrieve per page.

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
            f"/organizations/{org_id}/users/{id}/usergroups",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    user_get_user_groups_params.UserGetUserGroupsParams,
                ),
            ),
            cast_to=ResourceGroupResponse,
        )

    async def me(
        self,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserMeResponse:
        """
        Retrieve information about the current user

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
        return await self._get(
            f"/organizations/{org_id}/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserMeResponse,
        )

    async def resend_password(
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
    ) -> None:
        """
        Resend temporary password for user

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
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/organizations/{org_id}/users/{id}/password/resend",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class UsersResourceWithRawResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users

        self.retrieve = to_raw_response_wrapper(
            users.retrieve,
        )
        self.update = to_raw_response_wrapper(
            users.update,
        )
        self.list = to_raw_response_wrapper(
            users.list,
        )
        self.get_permissions = to_raw_response_wrapper(
            users.get_permissions,
        )
        self.get_user_groups = to_raw_response_wrapper(
            users.get_user_groups,
        )
        self.me = to_raw_response_wrapper(
            users.me,
        )
        self.resend_password = to_raw_response_wrapper(
            users.resend_password,
        )

    @cached_property
    def invitations(self) -> InvitationsResourceWithRawResponse:
        return InvitationsResourceWithRawResponse(self._users.invitations)


class AsyncUsersResourceWithRawResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users

        self.retrieve = async_to_raw_response_wrapper(
            users.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            users.update,
        )
        self.list = async_to_raw_response_wrapper(
            users.list,
        )
        self.get_permissions = async_to_raw_response_wrapper(
            users.get_permissions,
        )
        self.get_user_groups = async_to_raw_response_wrapper(
            users.get_user_groups,
        )
        self.me = async_to_raw_response_wrapper(
            users.me,
        )
        self.resend_password = async_to_raw_response_wrapper(
            users.resend_password,
        )

    @cached_property
    def invitations(self) -> AsyncInvitationsResourceWithRawResponse:
        return AsyncInvitationsResourceWithRawResponse(self._users.invitations)


class UsersResourceWithStreamingResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users

        self.retrieve = to_streamed_response_wrapper(
            users.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            users.update,
        )
        self.list = to_streamed_response_wrapper(
            users.list,
        )
        self.get_permissions = to_streamed_response_wrapper(
            users.get_permissions,
        )
        self.get_user_groups = to_streamed_response_wrapper(
            users.get_user_groups,
        )
        self.me = to_streamed_response_wrapper(
            users.me,
        )
        self.resend_password = to_streamed_response_wrapper(
            users.resend_password,
        )

    @cached_property
    def invitations(self) -> InvitationsResourceWithStreamingResponse:
        return InvitationsResourceWithStreamingResponse(self._users.invitations)


class AsyncUsersResourceWithStreamingResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users

        self.retrieve = async_to_streamed_response_wrapper(
            users.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            users.update,
        )
        self.list = async_to_streamed_response_wrapper(
            users.list,
        )
        self.get_permissions = async_to_streamed_response_wrapper(
            users.get_permissions,
        )
        self.get_user_groups = async_to_streamed_response_wrapper(
            users.get_user_groups,
        )
        self.me = async_to_streamed_response_wrapper(
            users.me,
        )
        self.resend_password = async_to_streamed_response_wrapper(
            users.resend_password,
        )

    @cached_property
    def invitations(self) -> AsyncInvitationsResourceWithStreamingResponse:
        return AsyncInvitationsResourceWithStreamingResponse(self._users.invitations)
