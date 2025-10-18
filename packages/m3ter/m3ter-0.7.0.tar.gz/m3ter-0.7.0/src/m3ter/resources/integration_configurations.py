# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict

import httpx

from ..types import (
    integration_configuration_list_params,
    integration_configuration_create_params,
    integration_configuration_update_params,
    integration_configuration_get_by_entity_params,
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
from ..types.integration_configuration_response import IntegrationConfigurationResponse
from ..types.integration_configuration_list_response import IntegrationConfigurationListResponse
from ..types.integration_configuration_create_response import IntegrationConfigurationCreateResponse
from ..types.integration_configuration_delete_response import IntegrationConfigurationDeleteResponse
from ..types.integration_configuration_enable_response import IntegrationConfigurationEnableResponse
from ..types.integration_configuration_update_response import IntegrationConfigurationUpdateResponse

__all__ = ["IntegrationConfigurationsResource", "AsyncIntegrationConfigurationsResource"]


class IntegrationConfigurationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> IntegrationConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return IntegrationConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IntegrationConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return IntegrationConfigurationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        destination: str,
        entity_type: str,
        config_data: Dict[str, object] | Omit = omit,
        credentials: integration_configuration_create_params.Credentials | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        integration_credentials_id: str | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationCreateResponse:
        """
        Set the integration configuration for the entity.

        Args:
          destination: Denotes the integration destination. This field identifies the target platform
              or service for the integration.

          entity_type: Specifies the type of entity for which the integration configuration is being
              updated. Must be a valid alphanumeric string.

          config_data: A flexible object to include any additional configuration data specific to the
              integration.

          credentials: Base model for defining integration credentials across different types of
              integrations.

          destination_id: The unique identifier (UUID) for the integration destination.

          entity_id: The unique identifier (UUID) of the entity. This field is used to specify which
              entity's integration configuration you're updating.

          integration_credentials_id

          name

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
            f"/organizations/{org_id}/integrationconfigs",
            body=maybe_transform(
                {
                    "destination": destination,
                    "entity_type": entity_type,
                    "config_data": config_data,
                    "credentials": credentials,
                    "destination_id": destination_id,
                    "entity_id": entity_id,
                    "integration_credentials_id": integration_credentials_id,
                    "name": name,
                    "version": version,
                },
                integration_configuration_create_params.IntegrationConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationCreateResponse,
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
    ) -> IntegrationConfigurationResponse:
        """
        Retrieve the integration configuration for the given UUID.

        This endpoint retrieves the configuration details of a specific integration
        within an organization. It is useful for obtaining the settings and parameters
        of an integration.

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        destination: str,
        entity_type: str,
        config_data: Dict[str, object] | Omit = omit,
        credentials: integration_configuration_update_params.Credentials | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        integration_credentials_id: str | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationUpdateResponse:
        """
        Update the integration configuration for the given UUID.

        This endpoint allows you to update the configuration of a specific integration
        within your organization. It is used to modify settings or parameters of an
        existing integration.

        Args:
          destination: Denotes the integration destination. This field identifies the target platform
              or service for the integration.

          entity_type: Specifies the type of entity for which the integration configuration is being
              updated. Must be a valid alphanumeric string.

          config_data: A flexible object to include any additional configuration data specific to the
              integration.

          credentials: Base model for defining integration credentials across different types of
              integrations.

          destination_id: The unique identifier (UUID) for the integration destination.

          entity_id: The unique identifier (UUID) of the entity. This field is used to specify which
              entity's integration configuration you're updating.

          integration_credentials_id

          name

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            body=maybe_transform(
                {
                    "destination": destination,
                    "entity_type": entity_type,
                    "config_data": config_data,
                    "credentials": credentials,
                    "destination_id": destination_id,
                    "entity_id": entity_id,
                    "integration_credentials_id": integration_credentials_id,
                    "name": name,
                    "version": version,
                },
                integration_configuration_update_params.IntegrationConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationUpdateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        destination_id: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[IntegrationConfigurationListResponse]:
        """
        List all integration configurations.

        This endpoint retrieves a list of all integration configurations for the
        specified Organization. The list can be paginated for easier management.

        Args:
          destination_id: optional filter for a specific destination

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              integration configurations in a paginated list.

          page_size: Specifies the maximum number of integration configurations to retrieve per page.

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
            f"/organizations/{org_id}/integrationconfigs",
            page=SyncCursor[IntegrationConfigurationListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "destination_id": destination_id,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    integration_configuration_list_params.IntegrationConfigurationListParams,
                ),
            ),
            model=IntegrationConfigurationListResponse,
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
    ) -> IntegrationConfigurationDeleteResponse:
        """
        Delete the integration configuration for the given UUID.

        Use this endpoint to delete the configuration of a specific integration within
        your organization. It is intended for removing integration settings that are no
        longer needed.

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationDeleteResponse,
        )

    def enable(
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
    ) -> IntegrationConfigurationEnableResponse:
        """
        Enables a previously disabled integration configuration, allowing it to be
        operational again.

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
        return self._post(
            f"/organizations/{org_id}/integrationconfigs/{id}/enable",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationEnableResponse,
        )

    def get_by_entity(
        self,
        entity_type: str,
        *,
        org_id: str | None = None,
        destination: str | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationResponse:
        """
        Retrieve the integration configuration for the entity

        Args:
          destination: Destination type to retrieve IntegrationConfigs for

          destination_id: UUID of the destination to retrieve IntegrationConfigs for

          entity_id: UUID of the entity to retrieve IntegrationConfigs for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not entity_type:
            raise ValueError(f"Expected a non-empty value for `entity_type` but received {entity_type!r}")
        return self._get(
            f"/organizations/{org_id}/integrationconfigs/entity/{entity_type}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "destination": destination,
                        "destination_id": destination_id,
                        "entity_id": entity_id,
                    },
                    integration_configuration_get_by_entity_params.IntegrationConfigurationGetByEntityParams,
                ),
            ),
            cast_to=IntegrationConfigurationResponse,
        )


class AsyncIntegrationConfigurationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncIntegrationConfigurationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncIntegrationConfigurationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIntegrationConfigurationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncIntegrationConfigurationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        destination: str,
        entity_type: str,
        config_data: Dict[str, object] | Omit = omit,
        credentials: integration_configuration_create_params.Credentials | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        integration_credentials_id: str | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationCreateResponse:
        """
        Set the integration configuration for the entity.

        Args:
          destination: Denotes the integration destination. This field identifies the target platform
              or service for the integration.

          entity_type: Specifies the type of entity for which the integration configuration is being
              updated. Must be a valid alphanumeric string.

          config_data: A flexible object to include any additional configuration data specific to the
              integration.

          credentials: Base model for defining integration credentials across different types of
              integrations.

          destination_id: The unique identifier (UUID) for the integration destination.

          entity_id: The unique identifier (UUID) of the entity. This field is used to specify which
              entity's integration configuration you're updating.

          integration_credentials_id

          name

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
            f"/organizations/{org_id}/integrationconfigs",
            body=await async_maybe_transform(
                {
                    "destination": destination,
                    "entity_type": entity_type,
                    "config_data": config_data,
                    "credentials": credentials,
                    "destination_id": destination_id,
                    "entity_id": entity_id,
                    "integration_credentials_id": integration_credentials_id,
                    "name": name,
                    "version": version,
                },
                integration_configuration_create_params.IntegrationConfigurationCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationCreateResponse,
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
    ) -> IntegrationConfigurationResponse:
        """
        Retrieve the integration configuration for the given UUID.

        This endpoint retrieves the configuration details of a specific integration
        within an organization. It is useful for obtaining the settings and parameters
        of an integration.

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        destination: str,
        entity_type: str,
        config_data: Dict[str, object] | Omit = omit,
        credentials: integration_configuration_update_params.Credentials | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        integration_credentials_id: str | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationUpdateResponse:
        """
        Update the integration configuration for the given UUID.

        This endpoint allows you to update the configuration of a specific integration
        within your organization. It is used to modify settings or parameters of an
        existing integration.

        Args:
          destination: Denotes the integration destination. This field identifies the target platform
              or service for the integration.

          entity_type: Specifies the type of entity for which the integration configuration is being
              updated. Must be a valid alphanumeric string.

          config_data: A flexible object to include any additional configuration data specific to the
              integration.

          credentials: Base model for defining integration credentials across different types of
              integrations.

          destination_id: The unique identifier (UUID) for the integration destination.

          entity_id: The unique identifier (UUID) of the entity. This field is used to specify which
              entity's integration configuration you're updating.

          integration_credentials_id

          name

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            body=await async_maybe_transform(
                {
                    "destination": destination,
                    "entity_type": entity_type,
                    "config_data": config_data,
                    "credentials": credentials,
                    "destination_id": destination_id,
                    "entity_id": entity_id,
                    "integration_credentials_id": integration_credentials_id,
                    "name": name,
                    "version": version,
                },
                integration_configuration_update_params.IntegrationConfigurationUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationUpdateResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        destination_id: str | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[IntegrationConfigurationListResponse, AsyncCursor[IntegrationConfigurationListResponse]]:
        """
        List all integration configurations.

        This endpoint retrieves a list of all integration configurations for the
        specified Organization. The list can be paginated for easier management.

        Args:
          destination_id: optional filter for a specific destination

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              integration configurations in a paginated list.

          page_size: Specifies the maximum number of integration configurations to retrieve per page.

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
            f"/organizations/{org_id}/integrationconfigs",
            page=AsyncCursor[IntegrationConfigurationListResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "destination_id": destination_id,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    integration_configuration_list_params.IntegrationConfigurationListParams,
                ),
            ),
            model=IntegrationConfigurationListResponse,
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
    ) -> IntegrationConfigurationDeleteResponse:
        """
        Delete the integration configuration for the given UUID.

        Use this endpoint to delete the configuration of a specific integration within
        your organization. It is intended for removing integration settings that are no
        longer needed.

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
            f"/organizations/{org_id}/integrationconfigs/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationDeleteResponse,
        )

    async def enable(
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
    ) -> IntegrationConfigurationEnableResponse:
        """
        Enables a previously disabled integration configuration, allowing it to be
        operational again.

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
        return await self._post(
            f"/organizations/{org_id}/integrationconfigs/{id}/enable",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IntegrationConfigurationEnableResponse,
        )

    async def get_by_entity(
        self,
        entity_type: str,
        *,
        org_id: str | None = None,
        destination: str | Omit = omit,
        destination_id: str | Omit = omit,
        entity_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IntegrationConfigurationResponse:
        """
        Retrieve the integration configuration for the entity

        Args:
          destination: Destination type to retrieve IntegrationConfigs for

          destination_id: UUID of the destination to retrieve IntegrationConfigs for

          entity_id: UUID of the entity to retrieve IntegrationConfigs for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not entity_type:
            raise ValueError(f"Expected a non-empty value for `entity_type` but received {entity_type!r}")
        return await self._get(
            f"/organizations/{org_id}/integrationconfigs/entity/{entity_type}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "destination": destination,
                        "destination_id": destination_id,
                        "entity_id": entity_id,
                    },
                    integration_configuration_get_by_entity_params.IntegrationConfigurationGetByEntityParams,
                ),
            ),
            cast_to=IntegrationConfigurationResponse,
        )


class IntegrationConfigurationsResourceWithRawResponse:
    def __init__(self, integration_configurations: IntegrationConfigurationsResource) -> None:
        self._integration_configurations = integration_configurations

        self.create = to_raw_response_wrapper(
            integration_configurations.create,
        )
        self.retrieve = to_raw_response_wrapper(
            integration_configurations.retrieve,
        )
        self.update = to_raw_response_wrapper(
            integration_configurations.update,
        )
        self.list = to_raw_response_wrapper(
            integration_configurations.list,
        )
        self.delete = to_raw_response_wrapper(
            integration_configurations.delete,
        )
        self.enable = to_raw_response_wrapper(
            integration_configurations.enable,
        )
        self.get_by_entity = to_raw_response_wrapper(
            integration_configurations.get_by_entity,
        )


class AsyncIntegrationConfigurationsResourceWithRawResponse:
    def __init__(self, integration_configurations: AsyncIntegrationConfigurationsResource) -> None:
        self._integration_configurations = integration_configurations

        self.create = async_to_raw_response_wrapper(
            integration_configurations.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            integration_configurations.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            integration_configurations.update,
        )
        self.list = async_to_raw_response_wrapper(
            integration_configurations.list,
        )
        self.delete = async_to_raw_response_wrapper(
            integration_configurations.delete,
        )
        self.enable = async_to_raw_response_wrapper(
            integration_configurations.enable,
        )
        self.get_by_entity = async_to_raw_response_wrapper(
            integration_configurations.get_by_entity,
        )


class IntegrationConfigurationsResourceWithStreamingResponse:
    def __init__(self, integration_configurations: IntegrationConfigurationsResource) -> None:
        self._integration_configurations = integration_configurations

        self.create = to_streamed_response_wrapper(
            integration_configurations.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            integration_configurations.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            integration_configurations.update,
        )
        self.list = to_streamed_response_wrapper(
            integration_configurations.list,
        )
        self.delete = to_streamed_response_wrapper(
            integration_configurations.delete,
        )
        self.enable = to_streamed_response_wrapper(
            integration_configurations.enable,
        )
        self.get_by_entity = to_streamed_response_wrapper(
            integration_configurations.get_by_entity,
        )


class AsyncIntegrationConfigurationsResourceWithStreamingResponse:
    def __init__(self, integration_configurations: AsyncIntegrationConfigurationsResource) -> None:
        self._integration_configurations = integration_configurations

        self.create = async_to_streamed_response_wrapper(
            integration_configurations.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            integration_configurations.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            integration_configurations.update,
        )
        self.list = async_to_streamed_response_wrapper(
            integration_configurations.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            integration_configurations.delete,
        )
        self.enable = async_to_streamed_response_wrapper(
            integration_configurations.enable,
        )
        self.get_by_entity = async_to_streamed_response_wrapper(
            integration_configurations.get_by_entity,
        )
