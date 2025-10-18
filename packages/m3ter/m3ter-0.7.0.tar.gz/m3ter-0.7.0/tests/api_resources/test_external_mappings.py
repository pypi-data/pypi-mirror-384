# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    ExternalMappingResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestExternalMappings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
            integration_config_id="00000000-0000-0000-0000-000000000000",
            version=0,
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.retrieve(
            id="id",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.external_mappings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
            integration_config_id="00000000-0000-0000-0000-000000000000",
            version=0,
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.external_mappings.with_raw_response.update(
                id="",
                external_id="cus_00000000000000",
                external_system="Stripe",
                external_table="Customer",
                m3ter_entity="Account",
                m3ter_id="00000000-0000-0000-0000-000000000000",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list()
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list(
            external_system_id="externalSystemId",
            integration_config_id="integrationConfigId",
            m3ter_ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.delete(
            id="id",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.external_mappings.with_raw_response.delete(
                id="",
            )

    @parametrize
    def test_method_list_by_external_entity(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        )
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_method_list_by_external_entity_with_all_params(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_raw_response_list_by_external_entity(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_list_by_external_entity(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list_by_external_entity(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `system` but received ''"):
            client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="externalId",
                system="",
                external_table="externalTable",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `external_table` but received ''"):
            client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="externalId",
                system="system",
                external_table="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `external_id` but received ''"):
            client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="",
                system="system",
                external_table="externalTable",
            )

    @parametrize
    def test_method_list_by_m3ter_entity(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        )
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_method_list_by_m3ter_entity_with_all_params(self, client: M3ter) -> None:
        external_mapping = client.external_mappings.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_raw_response_list_by_m3ter_entity(self, client: M3ter) -> None:
        response = client.external_mappings.with_raw_response.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = response.parse()
        assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    def test_streaming_response_list_by_m3ter_entity(self, client: M3ter) -> None:
        with client.external_mappings.with_streaming_response.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = response.parse()
            assert_matches_type(SyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list_by_m3ter_entity(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity` but received ''"):
            client.external_mappings.with_raw_response.list_by_m3ter_entity(
                m3ter_id="m3terId",
                entity="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `m3ter_id` but received ''"):
            client.external_mappings.with_raw_response.list_by_m3ter_entity(
                m3ter_id="",
                entity="entity",
            )


class TestAsyncExternalMappings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
            integration_config_id="00000000-0000-0000-0000-000000000000",
            version=0,
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.create(
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.retrieve(
            id="id",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.external_mappings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
            integration_config_id="00000000-0000-0000-0000-000000000000",
            version=0,
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.update(
            id="id",
            external_id="cus_00000000000000",
            external_system="Stripe",
            external_table="Customer",
            m3ter_entity="Account",
            m3ter_id="00000000-0000-0000-0000-000000000000",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.external_mappings.with_raw_response.update(
                id="",
                external_id="cus_00000000000000",
                external_system="Stripe",
                external_table="Customer",
                m3ter_entity="Account",
                m3ter_id="00000000-0000-0000-0000-000000000000",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list()
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list(
            external_system_id="externalSystemId",
            integration_config_id="integrationConfigId",
            m3ter_ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.delete(
            id="id",
        )
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(ExternalMappingResponse, external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.external_mappings.with_raw_response.delete(
                id="",
            )

    @parametrize
    async def test_method_list_by_external_entity(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        )
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_method_list_by_external_entity_with_all_params(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_list_by_external_entity(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_list_by_external_entity(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.list_by_external_entity(
            external_id="externalId",
            system="system",
            external_table="externalTable",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list_by_external_entity(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `system` but received ''"):
            await async_client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="externalId",
                system="",
                external_table="externalTable",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `external_table` but received ''"):
            await async_client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="externalId",
                system="system",
                external_table="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `external_id` but received ''"):
            await async_client.external_mappings.with_raw_response.list_by_external_entity(
                external_id="",
                system="system",
                external_table="externalTable",
            )

    @parametrize
    async def test_method_list_by_m3ter_entity(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        )
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_method_list_by_m3ter_entity_with_all_params(self, async_client: AsyncM3ter) -> None:
        external_mapping = await async_client.external_mappings.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_raw_response_list_by_m3ter_entity(self, async_client: AsyncM3ter) -> None:
        response = await async_client.external_mappings.with_raw_response.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        external_mapping = await response.parse()
        assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

    @parametrize
    async def test_streaming_response_list_by_m3ter_entity(self, async_client: AsyncM3ter) -> None:
        async with async_client.external_mappings.with_streaming_response.list_by_m3ter_entity(
            m3ter_id="m3terId",
            entity="entity",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            external_mapping = await response.parse()
            assert_matches_type(AsyncCursor[ExternalMappingResponse], external_mapping, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list_by_m3ter_entity(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `entity` but received ''"):
            await async_client.external_mappings.with_raw_response.list_by_m3ter_entity(
                m3ter_id="m3terId",
                entity="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `m3ter_id` but received ''"):
            await async_client.external_mappings.with_raw_response.list_by_m3ter_entity(
                m3ter_id="",
                entity="entity",
            )
