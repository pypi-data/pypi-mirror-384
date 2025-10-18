# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import CounterResponse
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCounters:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        counter = client.counters.create(
            name="x",
            unit="x",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        counter = client.counters.create(
            name="x",
            unit="x",
            code='S?oC"$]C] ]]]]]5]',
            product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.counters.with_raw_response.create(
            name="x",
            unit="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.counters.with_streaming_response.create(
            name="x",
            unit="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        counter = client.counters.retrieve(
            id="id",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.counters.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.counters.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counters.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        counter = client.counters.update(
            id="id",
            name="x",
            unit="x",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        counter = client.counters.update(
            id="id",
            name="x",
            unit="x",
            code='S?oC"$]C] ]]]]]5]',
            product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.counters.with_raw_response.update(
            id="id",
            name="x",
            unit="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.counters.with_streaming_response.update(
            id="id",
            name="x",
            unit="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counters.with_raw_response.update(
                id="",
                name="x",
                unit="x",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        counter = client.counters.list()
        assert_matches_type(SyncCursor[CounterResponse], counter, path=["response"])

    @pytest.mark.skip(reason="array parameter schemas need some work")
    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        counter = client.counters.list(
            codes=["string"],
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            product_id=["string"],
        )
        assert_matches_type(SyncCursor[CounterResponse], counter, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.counters.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = response.parse()
        assert_matches_type(SyncCursor[CounterResponse], counter, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.counters.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = response.parse()
            assert_matches_type(SyncCursor[CounterResponse], counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        counter = client.counters.delete(
            id="id",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.counters.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.counters.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counters.with_raw_response.delete(
                id="",
            )


class TestAsyncCounters:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.create(
            name="x",
            unit="x",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.create(
            name="x",
            unit="x",
            code='S?oC"$]C] ]]]]]5]',
            product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counters.with_raw_response.create(
            name="x",
            unit="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = await response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.counters.with_streaming_response.create(
            name="x",
            unit="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = await response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.retrieve(
            id="id",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counters.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = await response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.counters.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = await response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counters.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.update(
            id="id",
            name="x",
            unit="x",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.update(
            id="id",
            name="x",
            unit="x",
            code='S?oC"$]C] ]]]]]5]',
            product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counters.with_raw_response.update(
            id="id",
            name="x",
            unit="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = await response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.counters.with_streaming_response.update(
            id="id",
            name="x",
            unit="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = await response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counters.with_raw_response.update(
                id="",
                name="x",
                unit="x",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.list()
        assert_matches_type(AsyncCursor[CounterResponse], counter, path=["response"])

    @pytest.mark.skip(reason="array parameter schemas need some work")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.list(
            codes=["string"],
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            product_id=["string"],
        )
        assert_matches_type(AsyncCursor[CounterResponse], counter, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counters.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = await response.parse()
        assert_matches_type(AsyncCursor[CounterResponse], counter, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.counters.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = await response.parse()
            assert_matches_type(AsyncCursor[CounterResponse], counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        counter = await async_client.counters.delete(
            id="id",
        )
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counters.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter = await response.parse()
        assert_matches_type(CounterResponse, counter, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.counters.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter = await response.parse()
            assert_matches_type(CounterResponse, counter, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counters.with_raw_response.delete(
                id="",
            )
