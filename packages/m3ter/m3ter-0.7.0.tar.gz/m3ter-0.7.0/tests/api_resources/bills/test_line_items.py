# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.bills import LineItemResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLineItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        line_item = client.bills.line_items.retrieve(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    def test_method_retrieve_with_all_params(self, client: M3ter) -> None:
        line_item = client.bills.line_items.retrieve(
            id="id",
            bill_id="billId",
            additional=["string"],
        )
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.bills.line_items.with_raw_response.retrieve(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        line_item = response.parse()
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.bills.line_items.with_streaming_response.retrieve(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            line_item = response.parse()
            assert_matches_type(LineItemResponse, line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.line_items.with_raw_response.retrieve(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.line_items.with_raw_response.retrieve(
                id="",
                bill_id="billId",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        line_item = client.bills.line_items.list(
            bill_id="billId",
        )
        assert_matches_type(SyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        line_item = client.bills.line_items.list(
            bill_id="billId",
            additional=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.bills.line_items.with_raw_response.list(
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        line_item = response.parse()
        assert_matches_type(SyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.bills.line_items.with_streaming_response.list(
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            line_item = response.parse()
            assert_matches_type(SyncCursor[LineItemResponse], line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.line_items.with_raw_response.list(
                bill_id="",
            )


class TestAsyncLineItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        line_item = await async_client.bills.line_items.retrieve(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncM3ter) -> None:
        line_item = await async_client.bills.line_items.retrieve(
            id="id",
            bill_id="billId",
            additional=["string"],
        )
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.line_items.with_raw_response.retrieve(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        line_item = await response.parse()
        assert_matches_type(LineItemResponse, line_item, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.line_items.with_streaming_response.retrieve(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            line_item = await response.parse()
            assert_matches_type(LineItemResponse, line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.line_items.with_raw_response.retrieve(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.line_items.with_raw_response.retrieve(
                id="",
                bill_id="billId",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        line_item = await async_client.bills.line_items.list(
            bill_id="billId",
        )
        assert_matches_type(AsyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        line_item = await async_client.bills.line_items.list(
            bill_id="billId",
            additional=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.line_items.with_raw_response.list(
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        line_item = await response.parse()
        assert_matches_type(AsyncCursor[LineItemResponse], line_item, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.line_items.with_streaming_response.list(
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            line_item = await response.parse()
            assert_matches_type(AsyncCursor[LineItemResponse], line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.line_items.with_raw_response.list(
                bill_id="",
            )
