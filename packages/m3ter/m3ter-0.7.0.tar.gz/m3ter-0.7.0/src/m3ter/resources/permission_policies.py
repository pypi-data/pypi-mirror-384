# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ..types import (
    permission_policy_list_params,
    permission_policy_create_params,
    permission_policy_update_params,
    permission_policy_add_to_user_params,
    permission_policy_remove_from_user_params,
    permission_policy_add_to_user_group_params,
    permission_policy_add_to_service_user_params,
    permission_policy_add_to_support_user_params,
    permission_policy_remove_from_user_group_params,
    permission_policy_remove_from_service_user_params,
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
from ..types.permission_policy_response import PermissionPolicyResponse
from ..types.permission_statement_response_param import PermissionStatementResponseParam
from ..types.permission_policy_add_to_user_response import PermissionPolicyAddToUserResponse
from ..types.permission_policy_remove_from_user_response import PermissionPolicyRemoveFromUserResponse
from ..types.permission_policy_add_to_user_group_response import PermissionPolicyAddToUserGroupResponse
from ..types.permission_policy_add_to_service_user_response import PermissionPolicyAddToServiceUserResponse
from ..types.permission_policy_add_to_support_user_response import PermissionPolicyAddToSupportUserResponse
from ..types.permission_policy_remove_from_user_group_response import PermissionPolicyRemoveFromUserGroupResponse
from ..types.permission_policy_remove_from_service_user_response import PermissionPolicyRemoveFromServiceUserResponse
from ..types.permission_policy_remove_from_support_user_response import PermissionPolicyRemoveFromSupportUserResponse

__all__ = ["PermissionPoliciesResource", "AsyncPermissionPoliciesResource"]


class PermissionPoliciesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PermissionPoliciesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return PermissionPoliciesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PermissionPoliciesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return PermissionPoliciesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        permission_policy: Iterable[PermissionStatementResponseParam],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyResponse:
        """
        Create a new Permission Policy

        **NOTE:** When you set up a policy statement for this call using the
        `permissionPolicy` request parameter to specify the `effect`, `action`, and
        `resource`, you must use all lower case and the format as shown in this example
        for a Permission Policy statement that grants full CRUD access to all meters:

        ```
        "permissionPolicy" : [
                {
                        "effect" : "allow",
                        "action" : [
                        "config:create",
                        "config:delete",
                        "config:retrieve",
                        "config:update"
                        ]
                        "resource" : [
                        "config:meter/*"
                        ]
                }
        ]
        ```

        For more details and further examples, see
        [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions#permission-policy-statements---available-actions-and-resources)
        in our main Documentation.

        Args:
          name

          permission_policy

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - do not use
                for Create. On initial Create, version is set at 1 and listed in the response.
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
            f"/organizations/{org_id}/permissionpolicies",
            body=maybe_transform(
                {
                    "name": name,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                permission_policy_create_params.PermissionPolicyCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
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
    ) -> PermissionPolicyResponse:
        """
        Retrieve the permission policy for the UUID

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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        permission_policy: Iterable[PermissionStatementResponseParam],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyResponse:
        """
        Update a Permission Policy for the UUID

        **NOTE:** When you set up a policy statement for this call to specify the
        `effect`, `action`, and `resource`, you must use all lower case and the format
        as shown in this example - a Permission Policy statement that grants full CRUD
        access to all meters:

        ```
        "permissionPolicy" : [
                {
                        "effect" : "allow",
                        "action" : [
                        "config:create",
                        "config:delete",
                        "config:retrieve",
                        "config:update"
                        ]
                        "resource" : [
                        "config:meter/*"
                        ]
                }
        ]
        ```

        For more details and further examples, see
        [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions#permission-policy-statements---available-actions-and-resources)
        in our main Documentation.

        Args:
          name

          permission_policy

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - do not use
                for Create. On initial Create, version is set at 1 and listed in the response.
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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            body=maybe_transform(
                {
                    "name": name,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                permission_policy_update_params.PermissionPolicyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    def list(
        self,
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
    ) -> SyncCursor[PermissionPolicyResponse]:
        """
        Retrieve a list of PermissionPolicy entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of permission polices to retrieve per page

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
            f"/organizations/{org_id}/permissionpolicies",
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
                    permission_policy_list_params.PermissionPolicyListParams,
                ),
            ),
            model=PermissionPolicyResponse,
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
    ) -> PermissionPolicyResponse:
        """
        Delete the PermissionPolicy for the UUID

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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    def add_to_service_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToServiceUserResponse:
        """
        Add a permission policy to a service user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtoserviceuser",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_service_user_params.PermissionPolicyAddToServiceUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToServiceUserResponse,
        )

    def add_to_support_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToSupportUserResponse:
        """
        Add a permission policy to support users for an organization.

        Args:
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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtosupportusers",
            body=maybe_transform(
                {"version": version},
                permission_policy_add_to_support_user_params.PermissionPolicyAddToSupportUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToSupportUserResponse,
        )

    def add_to_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToUserResponse:
        """
        Add a permission policy to a user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtouser",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_user_params.PermissionPolicyAddToUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToUserResponse,
        )

    def add_to_user_group(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToUserGroupResponse:
        """
        Add a permission Policy to a user group

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtousergroup",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_user_group_params.PermissionPolicyAddToUserGroupParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToUserGroupResponse,
        )

    def remove_from_service_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromServiceUserResponse:
        """
        Remove a permission policy from a service user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromserviceuser",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_service_user_params.PermissionPolicyRemoveFromServiceUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromServiceUserResponse,
        )

    def remove_from_support_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromSupportUserResponse:
        """
        Remove a permission policy from support users for an organization.

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromsupportusers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromSupportUserResponse,
        )

    def remove_from_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromUserResponse:
        """
        Remove a permission policy from a user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromuser",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_user_params.PermissionPolicyRemoveFromUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromUserResponse,
        )

    def remove_from_user_group(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromUserGroupResponse:
        """
        Remove a permission policy from a user group.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromusergroup",
            body=maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_user_group_params.PermissionPolicyRemoveFromUserGroupParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromUserGroupResponse,
        )


class AsyncPermissionPoliciesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPermissionPoliciesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPermissionPoliciesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPermissionPoliciesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncPermissionPoliciesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        name: str,
        permission_policy: Iterable[PermissionStatementResponseParam],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyResponse:
        """
        Create a new Permission Policy

        **NOTE:** When you set up a policy statement for this call using the
        `permissionPolicy` request parameter to specify the `effect`, `action`, and
        `resource`, you must use all lower case and the format as shown in this example
        for a Permission Policy statement that grants full CRUD access to all meters:

        ```
        "permissionPolicy" : [
                {
                        "effect" : "allow",
                        "action" : [
                        "config:create",
                        "config:delete",
                        "config:retrieve",
                        "config:update"
                        ]
                        "resource" : [
                        "config:meter/*"
                        ]
                }
        ]
        ```

        For more details and further examples, see
        [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions#permission-policy-statements---available-actions-and-resources)
        in our main Documentation.

        Args:
          name

          permission_policy

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - do not use
                for Create. On initial Create, version is set at 1 and listed in the response.
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
            f"/organizations/{org_id}/permissionpolicies",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                permission_policy_create_params.PermissionPolicyCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
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
    ) -> PermissionPolicyResponse:
        """
        Retrieve the permission policy for the UUID

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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        name: str,
        permission_policy: Iterable[PermissionStatementResponseParam],
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyResponse:
        """
        Update a Permission Policy for the UUID

        **NOTE:** When you set up a policy statement for this call to specify the
        `effect`, `action`, and `resource`, you must use all lower case and the format
        as shown in this example - a Permission Policy statement that grants full CRUD
        access to all meters:

        ```
        "permissionPolicy" : [
                {
                        "effect" : "allow",
                        "action" : [
                        "config:create",
                        "config:delete",
                        "config:retrieve",
                        "config:update"
                        ]
                        "resource" : [
                        "config:meter/*"
                        ]
                }
        ]
        ```

        For more details and further examples, see
        [Understanding, Creating, and Managing Permission Policies](https://www.m3ter.com/docs/guides/organization-and-access-management/creating-and-managing-permissions#permission-policy-statements---available-actions-and-resources)
        in our main Documentation.

        Args:
          name

          permission_policy

          version:
              The version number of the entity:

              - **Create entity:** Not valid for initial insertion of new entity - do not use
                for Create. On initial Create, version is set at 1 and listed in the response.
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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "permission_policy": permission_policy,
                    "version": version,
                },
                permission_policy_update_params.PermissionPolicyUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    def list(
        self,
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
    ) -> AsyncPaginator[PermissionPolicyResponse, AsyncCursor[PermissionPolicyResponse]]:
        """
        Retrieve a list of PermissionPolicy entities

        Args:
          next_token: nextToken for multi page retrievals

          page_size: Number of permission polices to retrieve per page

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
            f"/organizations/{org_id}/permissionpolicies",
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
                    permission_policy_list_params.PermissionPolicyListParams,
                ),
            ),
            model=PermissionPolicyResponse,
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
    ) -> PermissionPolicyResponse:
        """
        Delete the PermissionPolicy for the UUID

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
            f"/organizations/{org_id}/permissionpolicies/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyResponse,
        )

    async def add_to_service_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToServiceUserResponse:
        """
        Add a permission policy to a service user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtoserviceuser",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_service_user_params.PermissionPolicyAddToServiceUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToServiceUserResponse,
        )

    async def add_to_support_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToSupportUserResponse:
        """
        Add a permission policy to support users for an organization.

        Args:
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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtosupportusers",
            body=await async_maybe_transform(
                {"version": version},
                permission_policy_add_to_support_user_params.PermissionPolicyAddToSupportUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToSupportUserResponse,
        )

    async def add_to_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToUserResponse:
        """
        Add a permission policy to a user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtouser",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_user_params.PermissionPolicyAddToUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToUserResponse,
        )

    async def add_to_user_group(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyAddToUserGroupResponse:
        """
        Add a permission Policy to a user group

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/addtousergroup",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_add_to_user_group_params.PermissionPolicyAddToUserGroupParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyAddToUserGroupResponse,
        )

    async def remove_from_service_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromServiceUserResponse:
        """
        Remove a permission policy from a service user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromserviceuser",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_service_user_params.PermissionPolicyRemoveFromServiceUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromServiceUserResponse,
        )

    async def remove_from_support_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromSupportUserResponse:
        """
        Remove a permission policy from support users for an organization.

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromsupportusers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromSupportUserResponse,
        )

    async def remove_from_user(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromUserResponse:
        """
        Remove a permission policy from a user.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromuser",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_user_params.PermissionPolicyRemoveFromUserParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromUserResponse,
        )

    async def remove_from_user_group(
        self,
        permission_policy_id: str,
        *,
        org_id: str | None = None,
        principal_id: str,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PermissionPolicyRemoveFromUserGroupResponse:
        """
        Remove a permission policy from a user group.

        Args:
          principal_id

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
        if not permission_policy_id:
            raise ValueError(
                f"Expected a non-empty value for `permission_policy_id` but received {permission_policy_id!r}"
            )
        return await self._post(
            f"/organizations/{org_id}/permissionpolicies/{permission_policy_id}/removefromusergroup",
            body=await async_maybe_transform(
                {
                    "principal_id": principal_id,
                    "version": version,
                },
                permission_policy_remove_from_user_group_params.PermissionPolicyRemoveFromUserGroupParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PermissionPolicyRemoveFromUserGroupResponse,
        )


class PermissionPoliciesResourceWithRawResponse:
    def __init__(self, permission_policies: PermissionPoliciesResource) -> None:
        self._permission_policies = permission_policies

        self.create = to_raw_response_wrapper(
            permission_policies.create,
        )
        self.retrieve = to_raw_response_wrapper(
            permission_policies.retrieve,
        )
        self.update = to_raw_response_wrapper(
            permission_policies.update,
        )
        self.list = to_raw_response_wrapper(
            permission_policies.list,
        )
        self.delete = to_raw_response_wrapper(
            permission_policies.delete,
        )
        self.add_to_service_user = to_raw_response_wrapper(
            permission_policies.add_to_service_user,
        )
        self.add_to_support_user = to_raw_response_wrapper(
            permission_policies.add_to_support_user,
        )
        self.add_to_user = to_raw_response_wrapper(
            permission_policies.add_to_user,
        )
        self.add_to_user_group = to_raw_response_wrapper(
            permission_policies.add_to_user_group,
        )
        self.remove_from_service_user = to_raw_response_wrapper(
            permission_policies.remove_from_service_user,
        )
        self.remove_from_support_user = to_raw_response_wrapper(
            permission_policies.remove_from_support_user,
        )
        self.remove_from_user = to_raw_response_wrapper(
            permission_policies.remove_from_user,
        )
        self.remove_from_user_group = to_raw_response_wrapper(
            permission_policies.remove_from_user_group,
        )


class AsyncPermissionPoliciesResourceWithRawResponse:
    def __init__(self, permission_policies: AsyncPermissionPoliciesResource) -> None:
        self._permission_policies = permission_policies

        self.create = async_to_raw_response_wrapper(
            permission_policies.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            permission_policies.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            permission_policies.update,
        )
        self.list = async_to_raw_response_wrapper(
            permission_policies.list,
        )
        self.delete = async_to_raw_response_wrapper(
            permission_policies.delete,
        )
        self.add_to_service_user = async_to_raw_response_wrapper(
            permission_policies.add_to_service_user,
        )
        self.add_to_support_user = async_to_raw_response_wrapper(
            permission_policies.add_to_support_user,
        )
        self.add_to_user = async_to_raw_response_wrapper(
            permission_policies.add_to_user,
        )
        self.add_to_user_group = async_to_raw_response_wrapper(
            permission_policies.add_to_user_group,
        )
        self.remove_from_service_user = async_to_raw_response_wrapper(
            permission_policies.remove_from_service_user,
        )
        self.remove_from_support_user = async_to_raw_response_wrapper(
            permission_policies.remove_from_support_user,
        )
        self.remove_from_user = async_to_raw_response_wrapper(
            permission_policies.remove_from_user,
        )
        self.remove_from_user_group = async_to_raw_response_wrapper(
            permission_policies.remove_from_user_group,
        )


class PermissionPoliciesResourceWithStreamingResponse:
    def __init__(self, permission_policies: PermissionPoliciesResource) -> None:
        self._permission_policies = permission_policies

        self.create = to_streamed_response_wrapper(
            permission_policies.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            permission_policies.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            permission_policies.update,
        )
        self.list = to_streamed_response_wrapper(
            permission_policies.list,
        )
        self.delete = to_streamed_response_wrapper(
            permission_policies.delete,
        )
        self.add_to_service_user = to_streamed_response_wrapper(
            permission_policies.add_to_service_user,
        )
        self.add_to_support_user = to_streamed_response_wrapper(
            permission_policies.add_to_support_user,
        )
        self.add_to_user = to_streamed_response_wrapper(
            permission_policies.add_to_user,
        )
        self.add_to_user_group = to_streamed_response_wrapper(
            permission_policies.add_to_user_group,
        )
        self.remove_from_service_user = to_streamed_response_wrapper(
            permission_policies.remove_from_service_user,
        )
        self.remove_from_support_user = to_streamed_response_wrapper(
            permission_policies.remove_from_support_user,
        )
        self.remove_from_user = to_streamed_response_wrapper(
            permission_policies.remove_from_user,
        )
        self.remove_from_user_group = to_streamed_response_wrapper(
            permission_policies.remove_from_user_group,
        )


class AsyncPermissionPoliciesResourceWithStreamingResponse:
    def __init__(self, permission_policies: AsyncPermissionPoliciesResource) -> None:
        self._permission_policies = permission_policies

        self.create = async_to_streamed_response_wrapper(
            permission_policies.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            permission_policies.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            permission_policies.update,
        )
        self.list = async_to_streamed_response_wrapper(
            permission_policies.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            permission_policies.delete,
        )
        self.add_to_service_user = async_to_streamed_response_wrapper(
            permission_policies.add_to_service_user,
        )
        self.add_to_support_user = async_to_streamed_response_wrapper(
            permission_policies.add_to_support_user,
        )
        self.add_to_user = async_to_streamed_response_wrapper(
            permission_policies.add_to_user,
        )
        self.add_to_user_group = async_to_streamed_response_wrapper(
            permission_policies.add_to_user_group,
        )
        self.remove_from_service_user = async_to_streamed_response_wrapper(
            permission_policies.remove_from_service_user,
        )
        self.remove_from_support_user = async_to_streamed_response_wrapper(
            permission_policies.remove_from_support_user,
        )
        self.remove_from_user = async_to_streamed_response_wrapper(
            permission_policies.remove_from_user,
        )
        self.remove_from_user_group = async_to_streamed_response_wrapper(
            permission_policies.remove_from_user_group,
        )
