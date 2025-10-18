# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.users import InvitationResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestInvitations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        invitation = client.users.invitations.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        invitation = client.users.invitations.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
            contact_number="contactNumber",
            dt_end_access=parse_datetime("2019-12-27T18:11:19.117Z"),
            dt_expiry=parse_datetime("2019-12-27T18:11:19.117Z"),
            m3ter_user=True,
            permission_policy_ids=["string"],
            version=0,
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.users.invitations.with_raw_response.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = response.parse()
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.users.invitations.with_streaming_response.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = response.parse()
            assert_matches_type(InvitationResponse, invitation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        invitation = client.users.invitations.retrieve(
            id="id",
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.users.invitations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = response.parse()
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.users.invitations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = response.parse()
            assert_matches_type(InvitationResponse, invitation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.users.invitations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        invitation = client.users.invitations.list()
        assert_matches_type(SyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        invitation = client.users.invitations.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.users.invitations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = response.parse()
        assert_matches_type(SyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.users.invitations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = response.parse()
            assert_matches_type(SyncCursor[InvitationResponse], invitation, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncInvitations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        invitation = await async_client.users.invitations.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        invitation = await async_client.users.invitations.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
            contact_number="contactNumber",
            dt_end_access=parse_datetime("2019-12-27T18:11:19.117Z"),
            dt_expiry=parse_datetime("2019-12-27T18:11:19.117Z"),
            m3ter_user=True,
            permission_policy_ids=["string"],
            version=0,
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.users.invitations.with_raw_response.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = await response.parse()
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.users.invitations.with_streaming_response.create(
            email="dev@stainless.com",
            first_name="x",
            last_name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = await response.parse()
            assert_matches_type(InvitationResponse, invitation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        invitation = await async_client.users.invitations.retrieve(
            id="id",
        )
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.users.invitations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = await response.parse()
        assert_matches_type(InvitationResponse, invitation, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.users.invitations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = await response.parse()
            assert_matches_type(InvitationResponse, invitation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.users.invitations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        invitation = await async_client.users.invitations.list()
        assert_matches_type(AsyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        invitation = await async_client.users.invitations.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.users.invitations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        invitation = await response.parse()
        assert_matches_type(AsyncCursor[InvitationResponse], invitation, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.users.invitations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            invitation = await response.parse()
            assert_matches_type(AsyncCursor[InvitationResponse], invitation, path=["response"])

        assert cast(Any, response.is_closed) is True
