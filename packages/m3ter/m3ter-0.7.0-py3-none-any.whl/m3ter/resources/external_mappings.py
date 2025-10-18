# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..types import (
    external_mapping_list_params,
    external_mapping_create_params,
    external_mapping_update_params,
    external_mapping_list_by_m3ter_entity_params,
    external_mapping_list_by_external_entity_params,
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
from ..types.external_mapping_response import ExternalMappingResponse

__all__ = ["ExternalMappingsResource", "AsyncExternalMappingsResource"]


class ExternalMappingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExternalMappingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return ExternalMappingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExternalMappingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return ExternalMappingsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        external_id: str,
        external_system: str,
        external_table: str,
        m3ter_entity: str,
        m3ter_id: str,
        integration_config_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalMappingResponse:
        """
        Creates a new External Mapping.

        This endpoint enables you to create a new External Mapping for the specified
        Organization. You need to supply a request body with the details of the new
        External Mapping.

        Args:
          external_id: The unique identifier (UUID) of the entity in the external system. This UUID
              should already exist in the external system.

          external_system: The name of the external system where the entity you are mapping resides.

          external_table: The name of the table in ther external system where the entity resides.

          m3ter_entity: The name of the m3ter entity that you are creating or modifying an External
              Mapping for. As an example, this could be an "Account".

          m3ter_id: The unique identifier (UUID) of the m3ter entity.

          integration_config_id: UUID of the integration config to link this mapping to

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
            f"/organizations/{org_id}/externalmappings",
            body=maybe_transform(
                {
                    "external_id": external_id,
                    "external_system": external_system,
                    "external_table": external_table,
                    "m3ter_entity": m3ter_entity,
                    "m3ter_id": m3ter_id,
                    "integration_config_id": integration_config_id,
                    "version": version,
                },
                external_mapping_create_params.ExternalMappingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
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
    ) -> ExternalMappingResponse:
        """
        Retrieve an External Mapping with the given UUID.

        This endpoint enables you to retrieve the External Mapping with the specified
        UUID for a specific Organization.

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
            f"/organizations/{org_id}/externalmappings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        external_id: str,
        external_system: str,
        external_table: str,
        m3ter_entity: str,
        m3ter_id: str,
        integration_config_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalMappingResponse:
        """
        Updates an External Mapping with the given UUID.

        This endpoint enables you to update an existing External Mapping entity,
        identified by its UUID. You must supply a request body with the new details for
        the External Mapping.

        Args:
          external_id: The unique identifier (UUID) of the entity in the external system. This UUID
              should already exist in the external system.

          external_system: The name of the external system where the entity you are mapping resides.

          external_table: The name of the table in ther external system where the entity resides.

          m3ter_entity: The name of the m3ter entity that you are creating or modifying an External
              Mapping for. As an example, this could be an "Account".

          m3ter_id: The unique identifier (UUID) of the m3ter entity.

          integration_config_id: UUID of the integration config to link this mapping to

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
            f"/organizations/{org_id}/externalmappings/{id}",
            body=maybe_transform(
                {
                    "external_id": external_id,
                    "external_system": external_system,
                    "external_table": external_table,
                    "m3ter_entity": m3ter_entity,
                    "m3ter_id": m3ter_id,
                    "integration_config_id": integration_config_id,
                    "version": version,
                },
                external_mapping_update_params.ExternalMappingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        external_system_id: str | Omit = omit,
        integration_config_id: str | Omit = omit,
        m3ter_ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ExternalMappingResponse]:
        """
        Retrieve a list of all External Mapping entities.

        This endpoint retrieves a list of all External Mapping entities for a specific
        Organization. The list can be paginated for better management, and supports
        filtering using the external system.

        Args:
          external_system_id: The name of the external system to use as a filter.

              For example, if you want to list only those external mappings created for your
              Organization for the Salesforce external system, use:

              `?externalSystemId=Salesforce`

          integration_config_id: ID of the integration config

          m3ter_ids: IDs for m3ter entities

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

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
            f"/organizations/{org_id}/externalmappings",
            page=SyncCursor[ExternalMappingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "external_system_id": external_system_id,
                        "integration_config_id": integration_config_id,
                        "m3ter_ids": m3ter_ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    external_mapping_list_params.ExternalMappingListParams,
                ),
            ),
            model=ExternalMappingResponse,
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
    ) -> ExternalMappingResponse:
        """
        Delete an External Mapping with the given UUID.

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
            f"/organizations/{org_id}/externalmappings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    def list_by_external_entity(
        self,
        external_id: str,
        *,
        org_id: str | None = None,
        system: str,
        external_table: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ExternalMappingResponse]:
        """
        Retrieve a list of External Mapping entities for a specified external system
        entity.

        Use this endpoint to retrieve a list of External Mapping entities associated
        with a specific external system entity. The list can be paginated for easier
        management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not system:
            raise ValueError(f"Expected a non-empty value for `system` but received {system!r}")
        if not external_table:
            raise ValueError(f"Expected a non-empty value for `external_table` but received {external_table!r}")
        if not external_id:
            raise ValueError(f"Expected a non-empty value for `external_id` but received {external_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/externalmappings/externalid/{system}/{external_table}/{external_id}",
            page=SyncCursor[ExternalMappingResponse],
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
                    external_mapping_list_by_external_entity_params.ExternalMappingListByExternalEntityParams,
                ),
            ),
            model=ExternalMappingResponse,
        )

    def list_by_m3ter_entity(
        self,
        m3ter_id: str,
        *,
        org_id: str | None = None,
        entity: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SyncCursor[ExternalMappingResponse]:
        """
        Retrieve a list of External Mapping entities for a specified m3ter entity.

        Use this endpoint to retrieve a list of External Mapping entities associated
        with a specific m3ter entity. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not entity:
            raise ValueError(f"Expected a non-empty value for `entity` but received {entity!r}")
        if not m3ter_id:
            raise ValueError(f"Expected a non-empty value for `m3ter_id` but received {m3ter_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/externalmappings/external/{entity}/{m3ter_id}",
            page=SyncCursor[ExternalMappingResponse],
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
                    external_mapping_list_by_m3ter_entity_params.ExternalMappingListByM3terEntityParams,
                ),
            ),
            model=ExternalMappingResponse,
        )


class AsyncExternalMappingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExternalMappingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncExternalMappingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExternalMappingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncExternalMappingsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        external_id: str,
        external_system: str,
        external_table: str,
        m3ter_entity: str,
        m3ter_id: str,
        integration_config_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalMappingResponse:
        """
        Creates a new External Mapping.

        This endpoint enables you to create a new External Mapping for the specified
        Organization. You need to supply a request body with the details of the new
        External Mapping.

        Args:
          external_id: The unique identifier (UUID) of the entity in the external system. This UUID
              should already exist in the external system.

          external_system: The name of the external system where the entity you are mapping resides.

          external_table: The name of the table in ther external system where the entity resides.

          m3ter_entity: The name of the m3ter entity that you are creating or modifying an External
              Mapping for. As an example, this could be an "Account".

          m3ter_id: The unique identifier (UUID) of the m3ter entity.

          integration_config_id: UUID of the integration config to link this mapping to

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
            f"/organizations/{org_id}/externalmappings",
            body=await async_maybe_transform(
                {
                    "external_id": external_id,
                    "external_system": external_system,
                    "external_table": external_table,
                    "m3ter_entity": m3ter_entity,
                    "m3ter_id": m3ter_id,
                    "integration_config_id": integration_config_id,
                    "version": version,
                },
                external_mapping_create_params.ExternalMappingCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
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
    ) -> ExternalMappingResponse:
        """
        Retrieve an External Mapping with the given UUID.

        This endpoint enables you to retrieve the External Mapping with the specified
        UUID for a specific Organization.

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
            f"/organizations/{org_id}/externalmappings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        external_id: str,
        external_system: str,
        external_table: str,
        m3ter_entity: str,
        m3ter_id: str,
        integration_config_id: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExternalMappingResponse:
        """
        Updates an External Mapping with the given UUID.

        This endpoint enables you to update an existing External Mapping entity,
        identified by its UUID. You must supply a request body with the new details for
        the External Mapping.

        Args:
          external_id: The unique identifier (UUID) of the entity in the external system. This UUID
              should already exist in the external system.

          external_system: The name of the external system where the entity you are mapping resides.

          external_table: The name of the table in ther external system where the entity resides.

          m3ter_entity: The name of the m3ter entity that you are creating or modifying an External
              Mapping for. As an example, this could be an "Account".

          m3ter_id: The unique identifier (UUID) of the m3ter entity.

          integration_config_id: UUID of the integration config to link this mapping to

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
            f"/organizations/{org_id}/externalmappings/{id}",
            body=await async_maybe_transform(
                {
                    "external_id": external_id,
                    "external_system": external_system,
                    "external_table": external_table,
                    "m3ter_entity": m3ter_entity,
                    "m3ter_id": m3ter_id,
                    "integration_config_id": integration_config_id,
                    "version": version,
                },
                external_mapping_update_params.ExternalMappingUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    def list(
        self,
        *,
        org_id: str | None = None,
        external_system_id: str | Omit = omit,
        integration_config_id: str | Omit = omit,
        m3ter_ids: SequenceNotStr[str] | Omit = omit,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ExternalMappingResponse, AsyncCursor[ExternalMappingResponse]]:
        """
        Retrieve a list of all External Mapping entities.

        This endpoint retrieves a list of all External Mapping entities for a specific
        Organization. The list can be paginated for better management, and supports
        filtering using the external system.

        Args:
          external_system_id: The name of the external system to use as a filter.

              For example, if you want to list only those external mappings created for your
              Organization for the Salesforce external system, use:

              `?externalSystemId=Salesforce`

          integration_config_id: ID of the integration config

          m3ter_ids: IDs for m3ter entities

          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

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
            f"/organizations/{org_id}/externalmappings",
            page=AsyncCursor[ExternalMappingResponse],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "external_system_id": external_system_id,
                        "integration_config_id": integration_config_id,
                        "m3ter_ids": m3ter_ids,
                        "next_token": next_token,
                        "page_size": page_size,
                    },
                    external_mapping_list_params.ExternalMappingListParams,
                ),
            ),
            model=ExternalMappingResponse,
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
    ) -> ExternalMappingResponse:
        """
        Delete an External Mapping with the given UUID.

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
            f"/organizations/{org_id}/externalmappings/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExternalMappingResponse,
        )

    def list_by_external_entity(
        self,
        external_id: str,
        *,
        org_id: str | None = None,
        system: str,
        external_table: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ExternalMappingResponse, AsyncCursor[ExternalMappingResponse]]:
        """
        Retrieve a list of External Mapping entities for a specified external system
        entity.

        Use this endpoint to retrieve a list of External Mapping entities associated
        with a specific external system entity. The list can be paginated for easier
        management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not system:
            raise ValueError(f"Expected a non-empty value for `system` but received {system!r}")
        if not external_table:
            raise ValueError(f"Expected a non-empty value for `external_table` but received {external_table!r}")
        if not external_id:
            raise ValueError(f"Expected a non-empty value for `external_id` but received {external_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/externalmappings/externalid/{system}/{external_table}/{external_id}",
            page=AsyncCursor[ExternalMappingResponse],
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
                    external_mapping_list_by_external_entity_params.ExternalMappingListByExternalEntityParams,
                ),
            ),
            model=ExternalMappingResponse,
        )

    def list_by_m3ter_entity(
        self,
        m3ter_id: str,
        *,
        org_id: str | None = None,
        entity: str,
        next_token: str | Omit = omit,
        page_size: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AsyncPaginator[ExternalMappingResponse, AsyncCursor[ExternalMappingResponse]]:
        """
        Retrieve a list of External Mapping entities for a specified m3ter entity.

        Use this endpoint to retrieve a list of External Mapping entities associated
        with a specific m3ter entity. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              External Mappings in a paginated list.

          page_size: Specifies the maximum number of External Mappings to retrieve per page.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if org_id is None:
            org_id = self._client._get_org_id_path_param()
        if not org_id:
            raise ValueError(f"Expected a non-empty value for `org_id` but received {org_id!r}")
        if not entity:
            raise ValueError(f"Expected a non-empty value for `entity` but received {entity!r}")
        if not m3ter_id:
            raise ValueError(f"Expected a non-empty value for `m3ter_id` but received {m3ter_id!r}")
        return self._get_api_list(
            f"/organizations/{org_id}/externalmappings/external/{entity}/{m3ter_id}",
            page=AsyncCursor[ExternalMappingResponse],
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
                    external_mapping_list_by_m3ter_entity_params.ExternalMappingListByM3terEntityParams,
                ),
            ),
            model=ExternalMappingResponse,
        )


class ExternalMappingsResourceWithRawResponse:
    def __init__(self, external_mappings: ExternalMappingsResource) -> None:
        self._external_mappings = external_mappings

        self.create = to_raw_response_wrapper(
            external_mappings.create,
        )
        self.retrieve = to_raw_response_wrapper(
            external_mappings.retrieve,
        )
        self.update = to_raw_response_wrapper(
            external_mappings.update,
        )
        self.list = to_raw_response_wrapper(
            external_mappings.list,
        )
        self.delete = to_raw_response_wrapper(
            external_mappings.delete,
        )
        self.list_by_external_entity = to_raw_response_wrapper(
            external_mappings.list_by_external_entity,
        )
        self.list_by_m3ter_entity = to_raw_response_wrapper(
            external_mappings.list_by_m3ter_entity,
        )


class AsyncExternalMappingsResourceWithRawResponse:
    def __init__(self, external_mappings: AsyncExternalMappingsResource) -> None:
        self._external_mappings = external_mappings

        self.create = async_to_raw_response_wrapper(
            external_mappings.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            external_mappings.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            external_mappings.update,
        )
        self.list = async_to_raw_response_wrapper(
            external_mappings.list,
        )
        self.delete = async_to_raw_response_wrapper(
            external_mappings.delete,
        )
        self.list_by_external_entity = async_to_raw_response_wrapper(
            external_mappings.list_by_external_entity,
        )
        self.list_by_m3ter_entity = async_to_raw_response_wrapper(
            external_mappings.list_by_m3ter_entity,
        )


class ExternalMappingsResourceWithStreamingResponse:
    def __init__(self, external_mappings: ExternalMappingsResource) -> None:
        self._external_mappings = external_mappings

        self.create = to_streamed_response_wrapper(
            external_mappings.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            external_mappings.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            external_mappings.update,
        )
        self.list = to_streamed_response_wrapper(
            external_mappings.list,
        )
        self.delete = to_streamed_response_wrapper(
            external_mappings.delete,
        )
        self.list_by_external_entity = to_streamed_response_wrapper(
            external_mappings.list_by_external_entity,
        )
        self.list_by_m3ter_entity = to_streamed_response_wrapper(
            external_mappings.list_by_m3ter_entity,
        )


class AsyncExternalMappingsResourceWithStreamingResponse:
    def __init__(self, external_mappings: AsyncExternalMappingsResource) -> None:
        self._external_mappings = external_mappings

        self.create = async_to_streamed_response_wrapper(
            external_mappings.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            external_mappings.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            external_mappings.update,
        )
        self.list = async_to_streamed_response_wrapper(
            external_mappings.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            external_mappings.delete,
        )
        self.list_by_external_entity = async_to_streamed_response_wrapper(
            external_mappings.list_by_external_entity,
        )
        self.list_by_m3ter_entity = async_to_streamed_response_wrapper(
            external_mappings.list_by_m3ter_entity,
        )
