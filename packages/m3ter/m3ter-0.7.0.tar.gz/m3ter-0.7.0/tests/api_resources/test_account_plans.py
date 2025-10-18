# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    AccountPlanResponse,
)
from tests.utils import assert_matches_type
from m3ter._utils import parse_date, parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAccountPlans:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        account_plan = client.account_plans.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        account_plan = client.account_plans.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            bill_epoch=parse_date("2019-12-27"),
            child_billing_mode="PARENT_SUMMARY",
            code='S?oC"$]C] ]]]]]5]',
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            custom_fields={"foo": "string"},
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_group_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            plan_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.account_plans.with_raw_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.account_plans.with_streaming_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        account_plan = client.account_plans.retrieve(
            id="id",
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.account_plans.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.account_plans.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.account_plans.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        account_plan = client.account_plans.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        account_plan = client.account_plans.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            bill_epoch=parse_date("2019-12-27"),
            child_billing_mode="PARENT_SUMMARY",
            code='S?oC"$]C] ]]]]]5]',
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            custom_fields={"foo": "string"},
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_group_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            plan_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.account_plans.with_raw_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.account_plans.with_streaming_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.account_plans.with_raw_response.update(
                id="",
                account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        account_plan = client.account_plans.list()
        assert_matches_type(SyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        account_plan = client.account_plans.list(
            account="account",
            contract="contract",
            date="date",
            ids=["string"],
            includeall=True,
            next_token="nextToken",
            page_size=1,
            plan="plan",
            product="product",
        )
        assert_matches_type(SyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.account_plans.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = response.parse()
        assert_matches_type(SyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.account_plans.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = response.parse()
            assert_matches_type(SyncCursor[AccountPlanResponse], account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        account_plan = client.account_plans.delete(
            id="id",
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.account_plans.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.account_plans.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.account_plans.with_raw_response.delete(
                id="",
            )


class TestAsyncAccountPlans:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            bill_epoch=parse_date("2019-12-27"),
            child_billing_mode="PARENT_SUMMARY",
            code='S?oC"$]C] ]]]]]5]',
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            custom_fields={"foo": "string"},
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_group_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            plan_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.account_plans.with_raw_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = await response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.account_plans.with_streaming_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = await response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.retrieve(
            id="id",
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.account_plans.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = await response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.account_plans.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = await response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.account_plans.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            bill_epoch=parse_date("2019-12-27"),
            child_billing_mode="PARENT_SUMMARY",
            code='S?oC"$]C] ]]]]]5]',
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            custom_fields={"foo": "string"},
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_group_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            plan_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            version=0,
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.account_plans.with_raw_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = await response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.account_plans.with_streaming_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = await response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.account_plans.with_raw_response.update(
                id="",
                account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.list()
        assert_matches_type(AsyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.list(
            account="account",
            contract="contract",
            date="date",
            ids=["string"],
            includeall=True,
            next_token="nextToken",
            page_size=1,
            plan="plan",
            product="product",
        )
        assert_matches_type(AsyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.account_plans.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = await response.parse()
        assert_matches_type(AsyncCursor[AccountPlanResponse], account_plan, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.account_plans.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = await response.parse()
            assert_matches_type(AsyncCursor[AccountPlanResponse], account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        account_plan = await async_client.account_plans.delete(
            id="id",
        )
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.account_plans.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account_plan = await response.parse()
        assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.account_plans.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account_plan = await response.parse()
            assert_matches_type(AccountPlanResponse, account_plan, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.account_plans.with_raw_response.delete(
                id="",
            )
