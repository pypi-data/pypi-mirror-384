# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    ScheduledEventConfigurationResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestScheduledEventConfigurations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
            version=0,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.scheduled_event_configurations.with_raw_response.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.scheduled_event_configurations.with_streaming_response.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.retrieve(
            id="id",
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.scheduled_event_configurations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.scheduled_event_configurations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.scheduled_event_configurations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
            version=0,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.scheduled_event_configurations.with_raw_response.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.scheduled_event_configurations.with_streaming_response.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.scheduled_event_configurations.with_raw_response.update(
                id="",
                entity="Bill",
                field="dueDate",
                name="10 Days After Bill Due Date",
                offset=10,
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.list()
        assert_matches_type(
            SyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.list(
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(
            SyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.scheduled_event_configurations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = response.parse()
        assert_matches_type(
            SyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.scheduled_event_configurations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = response.parse()
            assert_matches_type(
                SyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        scheduled_event_configuration = client.scheduled_event_configurations.delete(
            id="id",
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.scheduled_event_configurations.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.scheduled_event_configurations.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.scheduled_event_configurations.with_raw_response.delete(
                id="",
            )


class TestAsyncScheduledEventConfigurations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
            version=0,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.scheduled_event_configurations.with_raw_response.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = await response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.scheduled_event_configurations.with_streaming_response.create(
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = await response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.retrieve(
            id="id",
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.scheduled_event_configurations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = await response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.scheduled_event_configurations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = await response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.scheduled_event_configurations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
            version=0,
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.scheduled_event_configurations.with_raw_response.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = await response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.scheduled_event_configurations.with_streaming_response.update(
            id="id",
            entity="Bill",
            field="dueDate",
            name="10 Days After Bill Due Date",
            offset=10,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = await response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.scheduled_event_configurations.with_raw_response.update(
                id="",
                entity="Bill",
                field="dueDate",
                name="10 Days After Bill Due Date",
                offset=10,
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.list()
        assert_matches_type(
            AsyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.list(
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(
            AsyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.scheduled_event_configurations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = await response.parse()
        assert_matches_type(
            AsyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
        )

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.scheduled_event_configurations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = await response.parse()
            assert_matches_type(
                AsyncCursor[ScheduledEventConfigurationResponse], scheduled_event_configuration, path=["response"]
            )

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        scheduled_event_configuration = await async_client.scheduled_event_configurations.delete(
            id="id",
        )
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.scheduled_event_configurations.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        scheduled_event_configuration = await response.parse()
        assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.scheduled_event_configurations.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            scheduled_event_configuration = await response.parse()
            assert_matches_type(ScheduledEventConfigurationResponse, scheduled_event_configuration, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.scheduled_event_configurations.with_raw_response.delete(
                id="",
            )
