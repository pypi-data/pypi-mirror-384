# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime

import httpx

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
from ...types.users import invitation_list_params, invitation_create_params
from ..._base_client import AsyncPaginator, make_request_options
from ...types.users.invitation_response import InvitationResponse

__all__ = ["InvitationsResource", "AsyncInvitationsResource"]


class InvitationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> InvitationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return InvitationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> InvitationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return InvitationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        email: str,
        first_name: str,
        last_name: str,
        contact_number: str | Omit = omit,
        dt_end_access: Union[str, datetime] | Omit = omit,
        dt_expiry: Union[str, datetime] | Omit = omit,
        m3ter_user: bool | Omit = omit,
        permission_policy_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InvitationResponse:
        """
        Invite a new user to your Organization.

        This sends an email to someone inviting them to join your m3ter Organization.

        Args:
          email

          first_name

          last_name

          contact_number

          dt_end_access: The date when access will end for the user _(in ISO-8601 format)_. Leave blank
              for no end date, which gives the user permanent access.

          dt_expiry: The date when the invite expires _(in ISO-8601 format)_. After this date the
              invited user can no longer accept the invite. By default, any invite is valid
              for 30 days from the date the invite is sent.

          m3ter_user

          permission_policy_ids: The IDs of the permission policies the invited user has been assigned. This
              controls the access rights and privileges that this user will have when working
              in the m3ter Organization.

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
        return self._post(
            f"/organizations/{org_id}/invitations",
            body=maybe_transform(
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "contact_number": contact_number,
                    "dt_end_access": dt_end_access,
                    "dt_expiry": dt_expiry,
                    "m3ter_user": m3ter_user,
                    "permission_policy_ids": permission_policy_ids,
                    "version": version,
                },
                invitation_create_params.InvitationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvitationResponse,
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
    ) -> InvitationResponse:
        """
        Retrieve the specified invitation with the given UUID.

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
            f"/organizations/{org_id}/invitations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvitationResponse,
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
    ) -> SyncCursor[InvitationResponse]:
        """
        Retrieve a list of all invitations in the Organization.

        Args:
          next_token: `nextToken` for multi page retrievals.

          page_size: Number of invitations to retrieve per page.

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
            f"/organizations/{org_id}/invitations",
            page=SyncCursor[InvitationResponse],
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
                    invitation_list_params.InvitationListParams,
                ),
            ),
            model=InvitationResponse,
        )


class AsyncInvitationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncInvitationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncInvitationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncInvitationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncInvitationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        email: str,
        first_name: str,
        last_name: str,
        contact_number: str | Omit = omit,
        dt_end_access: Union[str, datetime] | Omit = omit,
        dt_expiry: Union[str, datetime] | Omit = omit,
        m3ter_user: bool | Omit = omit,
        permission_policy_ids: SequenceNotStr[str] | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InvitationResponse:
        """
        Invite a new user to your Organization.

        This sends an email to someone inviting them to join your m3ter Organization.

        Args:
          email

          first_name

          last_name

          contact_number

          dt_end_access: The date when access will end for the user _(in ISO-8601 format)_. Leave blank
              for no end date, which gives the user permanent access.

          dt_expiry: The date when the invite expires _(in ISO-8601 format)_. After this date the
              invited user can no longer accept the invite. By default, any invite is valid
              for 30 days from the date the invite is sent.

          m3ter_user

          permission_policy_ids: The IDs of the permission policies the invited user has been assigned. This
              controls the access rights and privileges that this user will have when working
              in the m3ter Organization.

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
        return await self._post(
            f"/organizations/{org_id}/invitations",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "contact_number": contact_number,
                    "dt_end_access": dt_end_access,
                    "dt_expiry": dt_expiry,
                    "m3ter_user": m3ter_user,
                    "permission_policy_ids": permission_policy_ids,
                    "version": version,
                },
                invitation_create_params.InvitationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvitationResponse,
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
    ) -> InvitationResponse:
        """
        Retrieve the specified invitation with the given UUID.

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
            f"/organizations/{org_id}/invitations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvitationResponse,
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
    ) -> AsyncPaginator[InvitationResponse, AsyncCursor[InvitationResponse]]:
        """
        Retrieve a list of all invitations in the Organization.

        Args:
          next_token: `nextToken` for multi page retrievals.

          page_size: Number of invitations to retrieve per page.

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
            f"/organizations/{org_id}/invitations",
            page=AsyncCursor[InvitationResponse],
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
                    invitation_list_params.InvitationListParams,
                ),
            ),
            model=InvitationResponse,
        )


class InvitationsResourceWithRawResponse:
    def __init__(self, invitations: InvitationsResource) -> None:
        self._invitations = invitations

        self.create = to_raw_response_wrapper(
            invitations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            invitations.retrieve,
        )
        self.list = to_raw_response_wrapper(
            invitations.list,
        )


class AsyncInvitationsResourceWithRawResponse:
    def __init__(self, invitations: AsyncInvitationsResource) -> None:
        self._invitations = invitations

        self.create = async_to_raw_response_wrapper(
            invitations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            invitations.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            invitations.list,
        )


class InvitationsResourceWithStreamingResponse:
    def __init__(self, invitations: InvitationsResource) -> None:
        self._invitations = invitations

        self.create = to_streamed_response_wrapper(
            invitations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            invitations.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            invitations.list,
        )


class AsyncInvitationsResourceWithStreamingResponse:
    def __init__(self, invitations: AsyncInvitationsResource) -> None:
        self._invitations = invitations

        self.create = async_to_streamed_response_wrapper(
            invitations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            invitations.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            invitations.list,
        )
