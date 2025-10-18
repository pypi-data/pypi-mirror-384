# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    EventResponse,
    EventGetTypesResponse,
    EventGetFieldsResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvents:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        event = client.events.retrieve(
            id="id",
        )
        assert_matches_type(EventResponse, event, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.events.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(EventResponse, event, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.events.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(EventResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.events.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        event = client.events.list()
        assert_matches_type(SyncCursor[EventResponse], event, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        event = client.events.list(
            account_id="accountId",
            event_name="eventName",
            event_type="eventType",
            ids=["string"],
            include_actioned=True,
            next_token="nextToken",
            notification_code="notificationCode",
            notification_id="notificationId",
            page_size=1,
            resource_id="resourceId",
        )
        assert_matches_type(SyncCursor[EventResponse], event, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.events.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(SyncCursor[EventResponse], event, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.events.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(SyncCursor[EventResponse], event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_get_fields(self, client: M3ter) -> None:
        event = client.events.get_fields()
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    def test_method_get_fields_with_all_params(self, client: M3ter) -> None:
        event = client.events.get_fields(
            event_name="eventName",
        )
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    def test_raw_response_get_fields(self, client: M3ter) -> None:
        response = client.events.with_raw_response.get_fields()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    def test_streaming_response_get_fields(self, client: M3ter) -> None:
        with client.events.with_streaming_response.get_fields() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(EventGetFieldsResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_get_types(self, client: M3ter) -> None:
        event = client.events.get_types()
        assert_matches_type(EventGetTypesResponse, event, path=["response"])

    @parametrize
    def test_raw_response_get_types(self, client: M3ter) -> None:
        response = client.events.with_raw_response.get_types()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = response.parse()
        assert_matches_type(EventGetTypesResponse, event, path=["response"])

    @parametrize
    def test_streaming_response_get_types(self, client: M3ter) -> None:
        with client.events.with_streaming_response.get_types() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = response.parse()
            assert_matches_type(EventGetTypesResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncEvents:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.retrieve(
            id="id",
        )
        assert_matches_type(EventResponse, event, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.events.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(EventResponse, event, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.events.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(EventResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.events.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.list()
        assert_matches_type(AsyncCursor[EventResponse], event, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.list(
            account_id="accountId",
            event_name="eventName",
            event_type="eventType",
            ids=["string"],
            include_actioned=True,
            next_token="nextToken",
            notification_code="notificationCode",
            notification_id="notificationId",
            page_size=1,
            resource_id="resourceId",
        )
        assert_matches_type(AsyncCursor[EventResponse], event, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.events.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(AsyncCursor[EventResponse], event, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.events.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(AsyncCursor[EventResponse], event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_get_fields(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.get_fields()
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    async def test_method_get_fields_with_all_params(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.get_fields(
            event_name="eventName",
        )
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    async def test_raw_response_get_fields(self, async_client: AsyncM3ter) -> None:
        response = await async_client.events.with_raw_response.get_fields()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(EventGetFieldsResponse, event, path=["response"])

    @parametrize
    async def test_streaming_response_get_fields(self, async_client: AsyncM3ter) -> None:
        async with async_client.events.with_streaming_response.get_fields() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(EventGetFieldsResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_get_types(self, async_client: AsyncM3ter) -> None:
        event = await async_client.events.get_types()
        assert_matches_type(EventGetTypesResponse, event, path=["response"])

    @parametrize
    async def test_raw_response_get_types(self, async_client: AsyncM3ter) -> None:
        response = await async_client.events.with_raw_response.get_types()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        event = await response.parse()
        assert_matches_type(EventGetTypesResponse, event, path=["response"])

    @parametrize
    async def test_streaming_response_get_types(self, async_client: AsyncM3ter) -> None:
        async with async_client.events.with_streaming_response.get_types() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            event = await response.parse()
            assert_matches_type(EventGetTypesResponse, event, path=["response"])

        assert cast(Any, response.is_closed) is True
