# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.statements import (
    StatementDefinitionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStatementDefinitions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.create(
            aggregation_frequency="DAY",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.create(
            aggregation_frequency="DAY",
            dimensions=[
                {
                    "filter": ["string"],
                    "name": "x",
                    "attributes": ["string"],
                    "meter_id": "meterId",
                }
            ],
            generate_slim_statements=True,
            include_price_per_unit=True,
            measures=[
                {
                    "aggregations": ["SUM"],
                    "meter_id": "meterId",
                    "name": "name",
                }
            ],
            name="name",
            version=0,
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.statements.statement_definitions.with_raw_response.create(
            aggregation_frequency="DAY",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.statements.statement_definitions.with_streaming_response.create(
            aggregation_frequency="DAY",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.retrieve(
            id="id",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.statements.statement_definitions.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.statements.statement_definitions.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.statement_definitions.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.update(
            id="id",
            aggregation_frequency="DAY",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.update(
            id="id",
            aggregation_frequency="DAY",
            dimensions=[
                {
                    "filter": ["string"],
                    "name": "x",
                    "attributes": ["string"],
                    "meter_id": "meterId",
                }
            ],
            generate_slim_statements=True,
            include_price_per_unit=True,
            measures=[
                {
                    "aggregations": ["SUM"],
                    "meter_id": "meterId",
                    "name": "name",
                }
            ],
            name="name",
            version=0,
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.statements.statement_definitions.with_raw_response.update(
            id="id",
            aggregation_frequency="DAY",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.statements.statement_definitions.with_streaming_response.update(
            id="id",
            aggregation_frequency="DAY",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.statement_definitions.with_raw_response.update(
                id="",
                aggregation_frequency="DAY",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.list()
        assert_matches_type(SyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.statements.statement_definitions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = response.parse()
        assert_matches_type(SyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.statements.statement_definitions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = response.parse()
            assert_matches_type(SyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        statement_definition = client.statements.statement_definitions.delete(
            id="id",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.statements.statement_definitions.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.statements.statement_definitions.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.statement_definitions.with_raw_response.delete(
                id="",
            )


class TestAsyncStatementDefinitions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.create(
            aggregation_frequency="DAY",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.create(
            aggregation_frequency="DAY",
            dimensions=[
                {
                    "filter": ["string"],
                    "name": "x",
                    "attributes": ["string"],
                    "meter_id": "meterId",
                }
            ],
            generate_slim_statements=True,
            include_price_per_unit=True,
            measures=[
                {
                    "aggregations": ["SUM"],
                    "meter_id": "meterId",
                    "name": "name",
                }
            ],
            name="name",
            version=0,
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_definitions.with_raw_response.create(
            aggregation_frequency="DAY",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = await response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_definitions.with_streaming_response.create(
            aggregation_frequency="DAY",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = await response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.retrieve(
            id="id",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_definitions.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = await response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_definitions.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = await response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.statement_definitions.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.update(
            id="id",
            aggregation_frequency="DAY",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.update(
            id="id",
            aggregation_frequency="DAY",
            dimensions=[
                {
                    "filter": ["string"],
                    "name": "x",
                    "attributes": ["string"],
                    "meter_id": "meterId",
                }
            ],
            generate_slim_statements=True,
            include_price_per_unit=True,
            measures=[
                {
                    "aggregations": ["SUM"],
                    "meter_id": "meterId",
                    "name": "name",
                }
            ],
            name="name",
            version=0,
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_definitions.with_raw_response.update(
            id="id",
            aggregation_frequency="DAY",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = await response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_definitions.with_streaming_response.update(
            id="id",
            aggregation_frequency="DAY",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = await response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.statement_definitions.with_raw_response.update(
                id="",
                aggregation_frequency="DAY",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.list()
        assert_matches_type(AsyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_definitions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = await response.parse()
        assert_matches_type(AsyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_definitions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = await response.parse()
            assert_matches_type(AsyncCursor[StatementDefinitionResponse], statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        statement_definition = await async_client.statements.statement_definitions.delete(
            id="id",
        )
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_definitions.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_definition = await response.parse()
        assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_definitions.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_definition = await response.parse()
            assert_matches_type(StatementDefinitionResponse, statement_definition, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.statement_definitions.with_raw_response.delete(
                id="",
            )
