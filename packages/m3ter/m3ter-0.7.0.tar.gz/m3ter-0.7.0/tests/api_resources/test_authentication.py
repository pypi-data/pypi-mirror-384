# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import AuthenticationGetBearerTokenResponse
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAuthentication:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_get_bearer_token(self, client: M3ter) -> None:
        authentication = client.authentication.get_bearer_token(
            grant_type="client_credentials",
        )
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    def test_method_get_bearer_token_with_all_params(self, client: M3ter) -> None:
        authentication = client.authentication.get_bearer_token(
            grant_type="client_credentials",
            scope="scope",
        )
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    def test_raw_response_get_bearer_token(self, client: M3ter) -> None:
        response = client.authentication.with_raw_response.get_bearer_token(
            grant_type="client_credentials",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        authentication = response.parse()
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    def test_streaming_response_get_bearer_token(self, client: M3ter) -> None:
        with client.authentication.with_streaming_response.get_bearer_token(
            grant_type="client_credentials",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            authentication = response.parse()
            assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAuthentication:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_get_bearer_token(self, async_client: AsyncM3ter) -> None:
        authentication = await async_client.authentication.get_bearer_token(
            grant_type="client_credentials",
        )
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    async def test_method_get_bearer_token_with_all_params(self, async_client: AsyncM3ter) -> None:
        authentication = await async_client.authentication.get_bearer_token(
            grant_type="client_credentials",
            scope="scope",
        )
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    async def test_raw_response_get_bearer_token(self, async_client: AsyncM3ter) -> None:
        response = await async_client.authentication.with_raw_response.get_bearer_token(
            grant_type="client_credentials",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        authentication = await response.parse()
        assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

    @parametrize
    async def test_streaming_response_get_bearer_token(self, async_client: AsyncM3ter) -> None:
        async with async_client.authentication.with_streaming_response.get_bearer_token(
            grant_type="client_credentials",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            authentication = await response.parse()
            assert_matches_type(AuthenticationGetBearerTokenResponse, authentication, path=["response"])

        assert cast(Any, response.is_closed) is True
