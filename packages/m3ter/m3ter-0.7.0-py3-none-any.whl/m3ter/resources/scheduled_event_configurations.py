# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import (
    scheduled_event_configuration_list_params,
    scheduled_event_configuration_create_params,
    scheduled_event_configuration_update_params,
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
from ..types.scheduled_event_configuration_response import ScheduledEventConfigurationResponse

__all__ = ["ScheduledEventConfigurationsResource", "AsyncScheduledEventConfigurationsResource"]


class ScheduledEventConfigurationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ScheduledEventConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ScheduledEventConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ScheduledEventConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ScheduledEventConfigurationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        entity: str,
        field: str,
        name: str,
        offset: int,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduledEventConfigurationResponse:
        """
        Create a new ScheduledEventConfiguration.

        Args:
          entity: The referenced configuration or billing entity for which the desired scheduled
              Event will trigger.

          field: A DateTime field for which the desired scheduled Event will trigger - this must
              be a DateTime field on the referenced billing or configuration entity.

          name: The name of the custom Scheduled Event Configuration.

              This must be in the format:

              - scheduled._name of entity_._custom event name_

              For example:

              - `scheduled.bill.endDateEvent`

          offset: The offset in days from the specified DateTime field on the referenced entity
              when the scheduled Event will trigger.

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
            f"/organizations/{org_id}/scheduledevents/configurations",
            body=maybe_transform(
                {
                    "entity": entity,
                    "field": field,
                    "name": name,
                    "offset": offset,
                    "version": version,
                },
                scheduled_event_configuration_create_params.ScheduledEventConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
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
    ) -> ScheduledEventConfigurationResponse:
        """
        Retrieve a ScheduledEventConfiguration for the given UUID.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        entity: str,
        field: str,
        name: str,
        offset: int,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduledEventConfigurationResponse:
        """
        Update a ScheduledEventConfiguration for the given UUID.

        Args:
          entity: The referenced configuration or billing entity for which the desired scheduled
              Event will trigger.

          field: A DateTime field for which the desired scheduled Event will trigger - this must
              be a DateTime field on the referenced billing or configuration entity.

          name: The name of the custom Scheduled Event Configuration.

              This must be in the format:

              - scheduled._name of entity_._custom event name_

              For example:

              - `scheduled.bill.endDateEvent`

          offset: The offset in days from the specified DateTime field on the referenced entity
              when the scheduled Event will trigger.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            body=maybe_transform(
                {
                    "entity": entity,
                    "field": field,
                    "name": name,
                    "offset": offset,
                    "version": version,
                },
                scheduled_event_configuration_update_params.ScheduledEventConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
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
    ) -> SyncCursor[ScheduledEventConfigurationResponse]:
        """
        Retrieve a list of ScheduledEventConfiguration entities

        Args:
          ids: list of UUIDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of ScheduledEventConfigurations to retrieve per page

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
            f"/organizations/{org_id}/scheduledevents/configurations",
            page=SyncCursor[ScheduledEventConfigurationResponse],
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
                    scheduled_event_configuration_list_params.ScheduledEventConfigurationListParams,
                ),
            ),
            model=ScheduledEventConfigurationResponse,
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
    ) -> ScheduledEventConfigurationResponse:
        """
        Delete the ScheduledEventConfiguration for the given UUID.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
        )


class AsyncScheduledEventConfigurationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncScheduledEventConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncScheduledEventConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncScheduledEventConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncScheduledEventConfigurationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        entity: str,
        field: str,
        name: str,
        offset: int,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduledEventConfigurationResponse:
        """
        Create a new ScheduledEventConfiguration.

        Args:
          entity: The referenced configuration or billing entity for which the desired scheduled
              Event will trigger.

          field: A DateTime field for which the desired scheduled Event will trigger - this must
              be a DateTime field on the referenced billing or configuration entity.

          name: The name of the custom Scheduled Event Configuration.

              This must be in the format:

              - scheduled._name of entity_._custom event name_

              For example:

              - `scheduled.bill.endDateEvent`

          offset: The offset in days from the specified DateTime field on the referenced entity
              when the scheduled Event will trigger.

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
            f"/organizations/{org_id}/scheduledevents/configurations",
            body=await async_maybe_transform(
                {
                    "entity": entity,
                    "field": field,
                    "name": name,
                    "offset": offset,
                    "version": version,
                },
                scheduled_event_configuration_create_params.ScheduledEventConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
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
    ) -> ScheduledEventConfigurationResponse:
        """
        Retrieve a ScheduledEventConfiguration for the given UUID.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        entity: str,
        field: str,
        name: str,
        offset: int,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ScheduledEventConfigurationResponse:
        """
        Update a ScheduledEventConfiguration for the given UUID.

        Args:
          entity: The referenced configuration or billing entity for which the desired scheduled
              Event will trigger.

          field: A DateTime field for which the desired scheduled Event will trigger - this must
              be a DateTime field on the referenced billing or configuration entity.

          name: The name of the custom Scheduled Event Configuration.

              This must be in the format:

              - scheduled._name of entity_._custom event name_

              For example:

              - `scheduled.bill.endDateEvent`

          offset: The offset in days from the specified DateTime field on the referenced entity
              when the scheduled Event will trigger.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            body=await async_maybe_transform(
                {
                    "entity": entity,
                    "field": field,
                    "name": name,
                    "offset": offset,
                    "version": version,
                },
                scheduled_event_configuration_update_params.ScheduledEventConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
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
    ) -> AsyncPaginator[ScheduledEventConfigurationResponse, AsyncCursor[ScheduledEventConfigurationResponse]]:
        """
        Retrieve a list of ScheduledEventConfiguration entities

        Args:
          ids: list of UUIDs to retrieve

          next_token: nextToken for multi page retrievals

          page_size: Number of ScheduledEventConfigurations to retrieve per page

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
            f"/organizations/{org_id}/scheduledevents/configurations",
            page=AsyncCursor[ScheduledEventConfigurationResponse],
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
                    scheduled_event_configuration_list_params.ScheduledEventConfigurationListParams,
                ),
            ),
            model=ScheduledEventConfigurationResponse,
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
    ) -> ScheduledEventConfigurationResponse:
        """
        Delete the ScheduledEventConfiguration for the given UUID.

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
            f"/organizations/{org_id}/scheduledevents/configurations/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ScheduledEventConfigurationResponse,
        )


class ScheduledEventConfigurationsResourceWithRawResponse:
    def __init__(self, scheduled_event_configurations: ScheduledEventConfigurationsResource) -> None:
        self._scheduled_event_configurations = scheduled_event_configurations

        self.create = to_raw_response_wrapper(
            scheduled_event_configurations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            scheduled_event_configurations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            scheduled_event_configurations.update,
        )
        self.list = to_raw_response_wrapper(
            scheduled_event_configurations.list,
        )
        self.delete = to_raw_response_wrapper(
            scheduled_event_configurations.delete,
        )


class AsyncScheduledEventConfigurationsResourceWithRawResponse:
    def __init__(self, scheduled_event_configurations: AsyncScheduledEventConfigurationsResource) -> None:
        self._scheduled_event_configurations = scheduled_event_configurations

        self.create = async_to_raw_response_wrapper(
            scheduled_event_configurations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            scheduled_event_configurations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            scheduled_event_configurations.update,
        )
        self.list = async_to_raw_response_wrapper(
            scheduled_event_configurations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            scheduled_event_configurations.delete,
        )


class ScheduledEventConfigurationsResourceWithStreamingResponse:
    def __init__(self, scheduled_event_configurations: ScheduledEventConfigurationsResource) -> None:
        self._scheduled_event_configurations = scheduled_event_configurations

        self.create = to_streamed_response_wrapper(
            scheduled_event_configurations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            scheduled_event_configurations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            scheduled_event_configurations.update,
        )
        self.list = to_streamed_response_wrapper(
            scheduled_event_configurations.list,
        )
        self.delete = to_streamed_response_wrapper(
            scheduled_event_configurations.delete,
        )


class AsyncScheduledEventConfigurationsResourceWithStreamingResponse:
    def __init__(self, scheduled_event_configurations: AsyncScheduledEventConfigurationsResource) -> None:
        self._scheduled_event_configurations = scheduled_event_configurations

        self.create = async_to_streamed_response_wrapper(
            scheduled_event_configurations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            scheduled_event_configurations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            scheduled_event_configurations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            scheduled_event_configurations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            scheduled_event_configurations.delete,
        )
