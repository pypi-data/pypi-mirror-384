# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ..._base_client import AsyncPaginator, make_request_options
from ...types.statements import (
    statement_definition_list_params,
    statement_definition_create_params,
    statement_definition_update_params,
)
from ...types.statements.statement_definition_response import StatementDefinitionResponse

__all__ = ["StatementDefinitionsResource", "AsyncStatementDefinitionsResource"]


class StatementDefinitionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StatementDefinitionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return StatementDefinitionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StatementDefinitionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return StatementDefinitionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        org_id: str | None = None,
        aggregation_frequency: Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"],
        dimensions: Iterable[statement_definition_create_params.Dimension] | Omit = omit,
        generate_slim_statements: bool | Omit = omit,
        include_price_per_unit: bool | Omit = omit,
        measures: Iterable[statement_definition_create_params.Measure] | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementDefinitionResponse:
        """
        Create a new StatementDefinition.

        This endpoint creates a new StatementDefinition within the specified
        Organization. The details of the StatementDefinition are provided in the request
        body.

        Args:
          aggregation_frequency: This specifies how often the Statement should aggregate data.

          dimensions: An array of objects, each representing a Dimension data field from a Meter _(for
              Meters that have Dimensions setup)_.

          generate_slim_statements

          include_price_per_unit: A Boolean indicating whether to include the price per unit in the Statement.

              - TRUE - includes the price per unit.
              - FALSE - excludes the price per unit.

          measures: An array of objects, each representing a Measure data field from a Meter.

          name: Descriptive name for the StatementDefinition providing context and information.

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
            f"/organizations/{org_id}/statementdefinitions",
            body=maybe_transform(
                {
                    "aggregation_frequency": aggregation_frequency,
                    "dimensions": dimensions,
                    "generate_slim_statements": generate_slim_statements,
                    "include_price_per_unit": include_price_per_unit,
                    "measures": measures,
                    "name": name,
                    "version": version,
                },
                statement_definition_create_params.StatementDefinitionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
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
    ) -> StatementDefinitionResponse:
        """
        Retrieve a StatementDefinition with the given UUID.

        Retrieves the details of a specific StatementDefinition for the specified
        Organization, using its unique identifier (UUID). This endpoint is useful when
        you want to retrieve the complete details of a single StatementDefinition.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
        )

    def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        aggregation_frequency: Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"],
        dimensions: Iterable[statement_definition_update_params.Dimension] | Omit = omit,
        generate_slim_statements: bool | Omit = omit,
        include_price_per_unit: bool | Omit = omit,
        measures: Iterable[statement_definition_update_params.Measure] | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementDefinitionResponse:
        """
        Update StatementDefinition for the given UUID.

        Update the details of a specific StatementDefinition for the specified
        Organization, using its unique identifier (UUID). The updated details for the
        StatementDefinition should be sent in the request body.

        Args:
          aggregation_frequency: This specifies how often the Statement should aggregate data.

          dimensions: An array of objects, each representing a Dimension data field from a Meter _(for
              Meters that have Dimensions setup)_.

          generate_slim_statements

          include_price_per_unit: A Boolean indicating whether to include the price per unit in the Statement.

              - TRUE - includes the price per unit.
              - FALSE - excludes the price per unit.

          measures: An array of objects, each representing a Measure data field from a Meter.

          name: Descriptive name for the StatementDefinition providing context and information.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            body=maybe_transform(
                {
                    "aggregation_frequency": aggregation_frequency,
                    "dimensions": dimensions,
                    "generate_slim_statements": generate_slim_statements,
                    "include_price_per_unit": include_price_per_unit,
                    "measures": measures,
                    "name": name,
                    "version": version,
                },
                statement_definition_update_params.StatementDefinitionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
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
    ) -> SyncCursor[StatementDefinitionResponse]:
        """
        Retrieve a list of StatementDefinitions.

        This endpoint retrieves a list of all the StatementDefinitions within a
        specified Organization. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              StatementDefinitions in a paginated list.

          page_size: Specifies the maximum number of StatementDefinitions to retrieve per page.

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
            f"/organizations/{org_id}/statementdefinitions",
            page=SyncCursor[StatementDefinitionResponse],
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
                    statement_definition_list_params.StatementDefinitionListParams,
                ),
            ),
            model=StatementDefinitionResponse,
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
    ) -> StatementDefinitionResponse:
        """
        Delete a StatementDefinition with the given UUID.

        This endpoint deletes a specific StatementDefinition within a specified
        Organization, using the StatementDefinition UUID.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
        )


class AsyncStatementDefinitionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStatementDefinitionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStatementDefinitionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStatementDefinitionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/m3ter-com/m3ter-sdk-python#with_streaming_response
        """
        return AsyncStatementDefinitionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        org_id: str | None = None,
        aggregation_frequency: Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"],
        dimensions: Iterable[statement_definition_create_params.Dimension] | Omit = omit,
        generate_slim_statements: bool | Omit = omit,
        include_price_per_unit: bool | Omit = omit,
        measures: Iterable[statement_definition_create_params.Measure] | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementDefinitionResponse:
        """
        Create a new StatementDefinition.

        This endpoint creates a new StatementDefinition within the specified
        Organization. The details of the StatementDefinition are provided in the request
        body.

        Args:
          aggregation_frequency: This specifies how often the Statement should aggregate data.

          dimensions: An array of objects, each representing a Dimension data field from a Meter _(for
              Meters that have Dimensions setup)_.

          generate_slim_statements

          include_price_per_unit: A Boolean indicating whether to include the price per unit in the Statement.

              - TRUE - includes the price per unit.
              - FALSE - excludes the price per unit.

          measures: An array of objects, each representing a Measure data field from a Meter.

          name: Descriptive name for the StatementDefinition providing context and information.

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
            f"/organizations/{org_id}/statementdefinitions",
            body=await async_maybe_transform(
                {
                    "aggregation_frequency": aggregation_frequency,
                    "dimensions": dimensions,
                    "generate_slim_statements": generate_slim_statements,
                    "include_price_per_unit": include_price_per_unit,
                    "measures": measures,
                    "name": name,
                    "version": version,
                },
                statement_definition_create_params.StatementDefinitionCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
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
    ) -> StatementDefinitionResponse:
        """
        Retrieve a StatementDefinition with the given UUID.

        Retrieves the details of a specific StatementDefinition for the specified
        Organization, using its unique identifier (UUID). This endpoint is useful when
        you want to retrieve the complete details of a single StatementDefinition.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
        )

    async def update(
        self,
        id: str,
        *,
        org_id: str | None = None,
        aggregation_frequency: Literal["DAY", "WEEK", "MONTH", "QUARTER", "YEAR", "WHOLE_PERIOD"],
        dimensions: Iterable[statement_definition_update_params.Dimension] | Omit = omit,
        generate_slim_statements: bool | Omit = omit,
        include_price_per_unit: bool | Omit = omit,
        measures: Iterable[statement_definition_update_params.Measure] | Omit = omit,
        name: str | Omit = omit,
        version: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StatementDefinitionResponse:
        """
        Update StatementDefinition for the given UUID.

        Update the details of a specific StatementDefinition for the specified
        Organization, using its unique identifier (UUID). The updated details for the
        StatementDefinition should be sent in the request body.

        Args:
          aggregation_frequency: This specifies how often the Statement should aggregate data.

          dimensions: An array of objects, each representing a Dimension data field from a Meter _(for
              Meters that have Dimensions setup)_.

          generate_slim_statements

          include_price_per_unit: A Boolean indicating whether to include the price per unit in the Statement.

              - TRUE - includes the price per unit.
              - FALSE - excludes the price per unit.

          measures: An array of objects, each representing a Measure data field from a Meter.

          name: Descriptive name for the StatementDefinition providing context and information.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            body=await async_maybe_transform(
                {
                    "aggregation_frequency": aggregation_frequency,
                    "dimensions": dimensions,
                    "generate_slim_statements": generate_slim_statements,
                    "include_price_per_unit": include_price_per_unit,
                    "measures": measures,
                    "name": name,
                    "version": version,
                },
                statement_definition_update_params.StatementDefinitionUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
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
    ) -> AsyncPaginator[StatementDefinitionResponse, AsyncCursor[StatementDefinitionResponse]]:
        """
        Retrieve a list of StatementDefinitions.

        This endpoint retrieves a list of all the StatementDefinitions within a
        specified Organization. The list can be paginated for easier management.

        Args:
          next_token: The `nextToken` for multi-page retrievals. It is used to fetch the next page of
              StatementDefinitions in a paginated list.

          page_size: Specifies the maximum number of StatementDefinitions to retrieve per page.

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
            f"/organizations/{org_id}/statementdefinitions",
            page=AsyncCursor[StatementDefinitionResponse],
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
                    statement_definition_list_params.StatementDefinitionListParams,
                ),
            ),
            model=StatementDefinitionResponse,
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
    ) -> StatementDefinitionResponse:
        """
        Delete a StatementDefinition with the given UUID.

        This endpoint deletes a specific StatementDefinition within a specified
        Organization, using the StatementDefinition UUID.

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
            f"/organizations/{org_id}/statementdefinitions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatementDefinitionResponse,
        )


class StatementDefinitionsResourceWithRawResponse:
    def __init__(self, statement_definitions: StatementDefinitionsResource) -> None:
        self._statement_definitions = statement_definitions

        self.create = to_raw_response_wrapper(
            statement_definitions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            statement_definitions.retrieve,
        )
        self.update = to_raw_response_wrapper(
            statement_definitions.update,
        )
        self.list = to_raw_response_wrapper(
            statement_definitions.list,
        )
        self.delete = to_raw_response_wrapper(
            statement_definitions.delete,
        )


class AsyncStatementDefinitionsResourceWithRawResponse:
    def __init__(self, statement_definitions: AsyncStatementDefinitionsResource) -> None:
        self._statement_definitions = statement_definitions

        self.create = async_to_raw_response_wrapper(
            statement_definitions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            statement_definitions.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            statement_definitions.update,
        )
        self.list = async_to_raw_response_wrapper(
            statement_definitions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            statement_definitions.delete,
        )


class StatementDefinitionsResourceWithStreamingResponse:
    def __init__(self, statement_definitions: StatementDefinitionsResource) -> None:
        self._statement_definitions = statement_definitions

        self.create = to_streamed_response_wrapper(
            statement_definitions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            statement_definitions.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            statement_definitions.update,
        )
        self.list = to_streamed_response_wrapper(
            statement_definitions.list,
        )
        self.delete = to_streamed_response_wrapper(
            statement_definitions.delete,
        )


class AsyncStatementDefinitionsResourceWithStreamingResponse:
    def __init__(self, statement_definitions: AsyncStatementDefinitionsResource) -> None:
        self._statement_definitions = statement_definitions

        self.create = async_to_streamed_response_wrapper(
            statement_definitions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            statement_definitions.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            statement_definitions.update,
        )
        self.list = async_to_streamed_response_wrapper(
            statement_definitions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            statement_definitions.delete,
        )
