# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import ObjectURLResponse
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStatements:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_csv(self, client: M3ter) -> None:
        statement = client.statements.create_csv(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_raw_response_create_csv(self, client: M3ter) -> None:
        response = client.statements.with_raw_response.create_csv(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_streaming_response_create_csv(self, client: M3ter) -> None:
        with client.statements.with_streaming_response.create_csv(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create_csv(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.with_raw_response.create_csv(
                id="",
            )

    @parametrize
    def test_method_get_csv(self, client: M3ter) -> None:
        statement = client.statements.get_csv(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_raw_response_get_csv(self, client: M3ter) -> None:
        response = client.statements.with_raw_response.get_csv(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_streaming_response_get_csv(self, client: M3ter) -> None:
        with client.statements.with_streaming_response.get_csv(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_get_csv(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.with_raw_response.get_csv(
                id="",
            )

    @parametrize
    def test_method_get_json(self, client: M3ter) -> None:
        statement = client.statements.get_json(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_raw_response_get_json(self, client: M3ter) -> None:
        response = client.statements.with_raw_response.get_json(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    def test_streaming_response_get_json(self, client: M3ter) -> None:
        with client.statements.with_streaming_response.get_json(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_get_json(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.with_raw_response.get_json(
                id="",
            )


class TestAsyncStatements:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_csv(self, async_client: AsyncM3ter) -> None:
        statement = await async_client.statements.create_csv(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_raw_response_create_csv(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.with_raw_response.create_csv(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = await response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_streaming_response_create_csv(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.with_streaming_response.create_csv(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = await response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create_csv(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.with_raw_response.create_csv(
                id="",
            )

    @parametrize
    async def test_method_get_csv(self, async_client: AsyncM3ter) -> None:
        statement = await async_client.statements.get_csv(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_raw_response_get_csv(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.with_raw_response.get_csv(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = await response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_streaming_response_get_csv(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.with_streaming_response.get_csv(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = await response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_get_csv(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.with_raw_response.get_csv(
                id="",
            )

    @parametrize
    async def test_method_get_json(self, async_client: AsyncM3ter) -> None:
        statement = await async_client.statements.get_json(
            id="id",
        )
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_raw_response_get_json(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.with_raw_response.get_json(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = await response.parse()
        assert_matches_type(ObjectURLResponse, statement, path=["response"])

    @parametrize
    async def test_streaming_response_get_json(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.with_streaming_response.get_json(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = await response.parse()
            assert_matches_type(ObjectURLResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_get_json(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.with_raw_response.get_json(
                id="",
            )
