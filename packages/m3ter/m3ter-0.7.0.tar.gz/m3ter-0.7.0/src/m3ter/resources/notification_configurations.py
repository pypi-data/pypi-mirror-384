# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import (
    notification_configuration_list_params,
    notification_configuration_create_params,
    notification_configuration_update_params,
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
from ..types.notification_configuration_response import NotificationConfigurationResponse

__all__ = ["NotificationConfigurationsResource", "AsyncNotificationConfigurationsResource"]


class NotificationConfigurationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NotificationConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return NotificationConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NotificationConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return NotificationConfigurationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        description: str,
        event_name: str,
        name: str,
        active: bool | Omit = omit,
        always_fire_event: bool | Omit = omit,
        calculation: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationConfigurationResponse:
        """
        Create a new Notification for an Event.

        This endpoint enables you to create a new Event Notification for the specified
        Organization. You need to supply a request body with the details of the new
        Notification.

        Args:
          code: The short code for the Notification.

          description: The description for the Notification providing a brief overview of its purpose
              and functionality.

          event_name: The name of the _Event type_ that the Notification is based on. When an Event of
              this type occurs and any calculation built into the Notification evaluates to
              `True`, the Notification is triggered.

              **Note:** If the Notification is set to always fire, then the Notification will
              always be sent when the Event of the type it is based on occurs, and without any
              other conditions defined by a calculation having to be met.

          name: The name of the Notification.

          active: Boolean flag that sets the Notification as active or inactive. Only active
              Notifications are sent when triggered by the Event they are based on:

              - **TRUE** - set Notification as active.
              - **FALSE** - set Notification as inactive.

          always_fire_event: A Boolean flag indicating whether the Notification is always triggered,
              regardless of other conditions and omitting reference to any calculation. This
              means the Notification will be triggered simply by the Event it is based on
              occurring and with no further conditions having to be met.

              - **TRUE** - the Notification is always triggered and omits any reference to the
                calculation to check for other conditions being true before triggering the
                Notification.
              - **FALSE** - the Notification is only triggered when the Event it is based on
                occurs and any calculation is checked and all conditions defined by the
                calculation are met.

          calculation: A logical expression that that is evaluated to a Boolean. If it evaluates as
              `True`, a Notification for the Event is created and sent to the configured
              destination. Calculations can reference numeric, string, and boolean Event
              fields.

              See
              [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/notifications/configurations",
            body=maybe_transform(
                {
                    "code": code,
                    "description": description,
                    "event_name": event_name,
                    "name": name,
                    "active": active,
                    "always_fire_event": always_fire_event,
                    "calculation": calculation,
                    "version": version,
                },
                notification_configuration_create_params.NotificationConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
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
    ) -> NotificationConfigurationResponse:
        """Retrieve the details of a specific Notification using its UUID.

        Includes the
        Event the Notification is based on, and any calculation referencing the Event's
        field and which defines further conditions that must be met to trigger the
        Notification when the Event occurs.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        description: str,
        event_name: str,
        name: str,
        active: bool | Omit = omit,
        always_fire_event: bool | Omit = omit,
        calculation: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationConfigurationResponse:
        """
        Update a Notification with the given UUID.

        This endpoint modifies the configuration details of an existing Notification.
        You can change the Event that triggers the Notification and/or update the
        conditions for sending the Notification.

        Args:
          code: The short code for the Notification.

          description: The description for the Notification providing a brief overview of its purpose
              and functionality.

          event_name: The name of the _Event type_ that the Notification is based on. When an Event of
              this type occurs and any calculation built into the Notification evaluates to
              `True`, the Notification is triggered.

              **Note:** If the Notification is set to always fire, then the Notification will
              always be sent when the Event of the type it is based on occurs, and without any
              other conditions defined by a calculation having to be met.

          name: The name of the Notification.

          active: Boolean flag that sets the Notification as active or inactive. Only active
              Notifications are sent when triggered by the Event they are based on:

              - **TRUE** - set Notification as active.
              - **FALSE** - set Notification as inactive.

          always_fire_event: A Boolean flag indicating whether the Notification is always triggered,
              regardless of other conditions and omitting reference to any calculation. This
              means the Notification will be triggered simply by the Event it is based on
              occurring and with no further conditions having to be met.

              - **TRUE** - the Notification is always triggered and omits any reference to the
                calculation to check for other conditions being true before triggering the
                Notification.
              - **FALSE** - the Notification is only triggered when the Event it is based on
                occurs and any calculation is checked and all conditions defined by the
                calculation are met.

          calculation: A logical expression that that is evaluated to a Boolean. If it evaluates as
              `True`, a Notification for the Event is created and sent to the configured
              destination. Calculations can reference numeric, string, and boolean Event
              fields.

              See
              [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            body=maybe_transform(
                {
                    "code": code,
                    "description": description,
                    "event_name": event_name,
                    "name": name,
                    "active": active,
                    "always_fire_event": always_fire_event,
                    "calculation": calculation,
                    "version": version,
                },
                notification_configuration_update_params.NotificationConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: bool | Omit = omit,
        event_name: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[NotificationConfigurationResponse]:
        """
        Retrieve a list of Event Notifications for the specified Organization.

        This endpoint retrieves a list of all Event Notifications for the Organization
        identified by its UUID. The list can be paginated for easier management. The
        list also supports filtering by parameters such as Notification UUID.

        Args:
          active: A Boolean flag indicating whether to retrieve only active or only inactive
              Notifications.

              - **TRUE** - only active Notifications are returned.
              - **FALSE** - only inactive Notifications are returned.

          event_name: Use this to filter the Notifications returned - only those Notifications that
              are based on the _Event type_ specified by `eventName` are returned.

          ids: A list of specific Notification UUIDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Notifications in a paginated list.

          page_size: Specifies the maximum number of Notifications to retrieve per page.

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
            f"/organizations/{org_id}/notifications/configurations",
            page=SyncCursor[NotificationConfigurationResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "event_name": event_name,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    notification_configuration_list_params.NotificationConfigurationListParams,
                ),
            ),
            model=NotificationConfigurationResponse,
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
    ) -> NotificationConfigurationResponse:
        """
        Delete the Notification with the given UUID.

        This endpoint permanently removes a specified Notification and its
        configuration. This action cannot be undone.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )


class AsyncNotificationConfigurationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNotificationConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncNotificationConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNotificationConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncNotificationConfigurationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        code: str,
        description: str,
        event_name: str,
        name: str,
        active: bool | Omit = omit,
        always_fire_event: bool | Omit = omit,
        calculation: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationConfigurationResponse:
        """
        Create a new Notification for an Event.

        This endpoint enables you to create a new Event Notification for the specified
        Organization. You need to supply a request body with the details of the new
        Notification.

        Args:
          code: The short code for the Notification.

          description: The description for the Notification providing a brief overview of its purpose
              and functionality.

          event_name: The name of the _Event type_ that the Notification is based on. When an Event of
              this type occurs and any calculation built into the Notification evaluates to
              `True`, the Notification is triggered.

              **Note:** If the Notification is set to always fire, then the Notification will
              always be sent when the Event of the type it is based on occurs, and without any
              other conditions defined by a calculation having to be met.

          name: The name of the Notification.

          active: Boolean flag that sets the Notification as active or inactive. Only active
              Notifications are sent when triggered by the Event they are based on:

              - **TRUE** - set Notification as active.
              - **FALSE** - set Notification as inactive.

          always_fire_event: A Boolean flag indicating whether the Notification is always triggered,
              regardless of other conditions and omitting reference to any calculation. This
              means the Notification will be triggered simply by the Event it is based on
              occurring and with no further conditions having to be met.

              - **TRUE** - the Notification is always triggered and omits any reference to the
                calculation to check for other conditions being true before triggering the
                Notification.
              - **FALSE** - the Notification is only triggered when the Event it is based on
                occurs and any calculation is checked and all conditions defined by the
                calculation are met.

          calculation: A logical expression that that is evaluated to a Boolean. If it evaluates as
              `True`, a Notification for the Event is created and sent to the configured
              destination. Calculations can reference numeric, string, and boolean Event
              fields.

              See
              [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/notifications/configurations",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "description": description,
                    "event_name": event_name,
                    "name": name,
                    "active": active,
                    "always_fire_event": always_fire_event,
                    "calculation": calculation,
                    "version": version,
                },
                notification_configuration_create_params.NotificationConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
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
    ) -> NotificationConfigurationResponse:
        """Retrieve the details of a specific Notification using its UUID.

        Includes the
        Event the Notification is based on, and any calculation referencing the Event's
        field and which defines further conditions that must be met to trigger the
        Notification when the Event occurs.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        code: str,
        description: str,
        event_name: str,
        name: str,
        active: bool | Omit = omit,
        always_fire_event: bool | Omit = omit,
        calculation: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationConfigurationResponse:
        """
        Update a Notification with the given UUID.

        This endpoint modifies the configuration details of an existing Notification.
        You can change the Event that triggers the Notification and/or update the
        conditions for sending the Notification.

        Args:
          code: The short code for the Notification.

          description: The description for the Notification providing a brief overview of its purpose
              and functionality.

          event_name: The name of the _Event type_ that the Notification is based on. When an Event of
              this type occurs and any calculation built into the Notification evaluates to
              `True`, the Notification is triggered.

              **Note:** If the Notification is set to always fire, then the Notification will
              always be sent when the Event of the type it is based on occurs, and without any
              other conditions defined by a calculation having to be met.

          name: The name of the Notification.

          active: Boolean flag that sets the Notification as active or inactive. Only active
              Notifications are sent when triggered by the Event they are based on:

              - **TRUE** - set Notification as active.
              - **FALSE** - set Notification as inactive.

          always_fire_event: A Boolean flag indicating whether the Notification is always triggered,
              regardless of other conditions and omitting reference to any calculation. This
              means the Notification will be triggered simply by the Event it is based on
              occurring and with no further conditions having to be met.

              - **TRUE** - the Notification is always triggered and omits any reference to the
                calculation to check for other conditions being true before triggering the
                Notification.
              - **FALSE** - the Notification is only triggered when the Event it is based on
                occurs and any calculation is checked and all conditions defined by the
                calculation are met.

          calculation: A logical expression that that is evaluated to a Boolean. If it evaluates as
              `True`, a Notification for the Event is created and sent to the configured
              destination. Calculations can reference numeric, string, and boolean Event
              fields.

              See
              [Creating Calculations](https://www.m3ter.com/docs/guides/utilizing-events-and-notifications/key-concepts-and-relationships#creating-calculations)
              in the m3ter documentation for more information.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            body=await async_maybe_transform(
                {
                    "code": code,
                    "description": description,
                    "event_name": event_name,
                    "name": name,
                    "active": active,
                    "always_fire_event": always_fire_event,
                    "calculation": calculation,
                    "version": version,
                },
                notification_configuration_update_params.NotificationConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        active: bool | Omit = omit,
        event_name: str | Omit = omit,
        ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[NotificationConfigurationResponse, AsyncCursor[NotificationConfigurationResponse]]:
        """
        Retrieve a list of Event Notifications for the specified Organization.

        This endpoint retrieves a list of all Event Notifications for the Organization
        identified by its UUID. The list can be paginated for easier management. The
        list also supports filtering by parameters such as Notification UUID.

        Args:
          active: A Boolean flag indicating whether to retrieve only active or only inactive
              Notifications.

              - **TRUE** - only active Notifications are returned.
              - **FALSE** - only inactive Notifications are returned.

          event_name: Use this to filter the Notifications returned - only those Notifications that
              are based on the _Event type_ specified by `eventName` are returned.

          ids: A list of specific Notification UUIDs to retrieve.

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              Notifications in a paginated list.

          page_size: Specifies the maximum number of Notifications to retrieve per page.

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
            f"/organizations/{org_id}/notifications/configurations",
            page=AsyncCursor[NotificationConfigurationResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "active": active,
                        "event_name": event_name,
                        "ids": ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    notification_configuration_list_params.NotificationConfigurationListParams,
                ),
            ),
            model=NotificationConfigurationResponse,
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
    ) -> NotificationConfigurationResponse:
        """
        Delete the Notification with the given UUID.

        This endpoint permanently removes a specified Notification and its
        configuration. This action cannot be undone.

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
            f"/organizations/{org_id}/notifications/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationConfigurationResponse,
        )


class NotificationConfigurationsResourceWithRawResponse:
    def __init__(self, notification_configurations: NotificationConfigurationsResource) -> None:
        self._notification_configurations = notification_configurations

        self.create = to_raw_response_wrapper(
            notification_configurations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            notification_configurations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            notification_configurations.update,
        )
        self.list = to_raw_response_wrapper(
            notification_configurations.list,
        )
        self.delete = to_raw_response_wrapper(
            notification_configurations.delete,
        )


class AsyncNotificationConfigurationsResourceWithRawResponse:
    def __init__(self, notification_configurations: AsyncNotificationConfigurationsResource) -> None:
        self._notification_configurations = notification_configurations

        self.create = async_to_raw_response_wrapper(
            notification_configurations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            notification_configurations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            notification_configurations.update,
        )
        self.list = async_to_raw_response_wrapper(
            notification_configurations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            notification_configurations.delete,
        )


class NotificationConfigurationsResourceWithStreamingResponse:
    def __init__(self, notification_configurations: NotificationConfigurationsResource) -> None:
        self._notification_configurations = notification_configurations

        self.create = to_streamed_response_wrapper(
            notification_configurations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            notification_configurations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            notification_configurations.update,
        )
        self.list = to_streamed_response_wrapper(
            notification_configurations.list,
        )
        self.delete = to_streamed_response_wrapper(
            notification_configurations.delete,
        )


class AsyncNotificationConfigurationsResourceWithStreamingResponse:
    def __init__(self, notification_configurations: AsyncNotificationConfigurationsResource) -> None:
        self._notification_configurations = notification_configurations

        self.create = async_to_streamed_response_wrapper(
            notification_configurations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            notification_configurations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            notification_configurations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            notification_configurations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            notification_configurations.delete,
        )
