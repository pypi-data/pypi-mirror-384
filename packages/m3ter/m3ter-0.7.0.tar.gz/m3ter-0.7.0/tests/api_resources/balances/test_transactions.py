# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.balances import (
    TransactionResponse,
    TransactionSummaryResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTransactions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        transaction = client.balances.transactions.create(
            balance_id="balanceId",
            amount=0,
        )
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        transaction = client.balances.transactions.create(
            balance_id="balanceId",
            amount=0,
            applied_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            currency_paid="currencyPaid",
            description="description",
            paid=0,
            transaction_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            transaction_type_id="transactionTypeId",
            version=0,
        )
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.balances.transactions.with_raw_response.create(
            balance_id="balanceId",
            amount=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.balances.transactions.with_streaming_response.create(
            balance_id="balanceId",
            amount=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.transactions.with_raw_response.create(
                balance_id="",
                amount=0,
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        transaction = client.balances.transactions.list(
            balance_id="balanceId",
        )
        assert_matches_type(SyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        transaction = client.balances.transactions.list(
            balance_id="balanceId",
            entity_id="entityId",
            entity_type="BILL",
            next_token="nextToken",
            page_size=1,
            transaction_type_id="transactionTypeId",
        )
        assert_matches_type(SyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.balances.transactions.with_raw_response.list(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(SyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.balances.transactions.with_streaming_response.list(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(SyncCursor[TransactionResponse], transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.transactions.with_raw_response.list(
                balance_id="",
            )

    @parametrize
    def test_method_summary(self, client: M3ter) -> None:
        transaction = client.balances.transactions.summary(
            balance_id="balanceId",
        )
        assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

    @parametrize
    def test_raw_response_summary(self, client: M3ter) -> None:
        response = client.balances.transactions.with_raw_response.summary(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

    @parametrize
    def test_streaming_response_summary(self, client: M3ter) -> None:
        with client.balances.transactions.with_streaming_response.summary(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_summary(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            client.balances.transactions.with_raw_response.summary(
                balance_id="",
            )


class TestAsyncTransactions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        transaction = await async_client.balances.transactions.create(
            balance_id="balanceId",
            amount=0,
        )
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        transaction = await async_client.balances.transactions.create(
            balance_id="balanceId",
            amount=0,
            applied_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            currency_paid="currencyPaid",
            description="description",
            paid=0,
            transaction_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            transaction_type_id="transactionTypeId",
            version=0,
        )
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.transactions.with_raw_response.create(
            balance_id="balanceId",
            amount=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionResponse, transaction, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.transactions.with_streaming_response.create(
            balance_id="balanceId",
            amount=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.transactions.with_raw_response.create(
                balance_id="",
                amount=0,
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        transaction = await async_client.balances.transactions.list(
            balance_id="balanceId",
        )
        assert_matches_type(AsyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        transaction = await async_client.balances.transactions.list(
            balance_id="balanceId",
            entity_id="entityId",
            entity_type="BILL",
            next_token="nextToken",
            page_size=1,
            transaction_type_id="transactionTypeId",
        )
        assert_matches_type(AsyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.transactions.with_raw_response.list(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(AsyncCursor[TransactionResponse], transaction, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.transactions.with_streaming_response.list(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(AsyncCursor[TransactionResponse], transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.transactions.with_raw_response.list(
                balance_id="",
            )

    @parametrize
    async def test_method_summary(self, async_client: AsyncM3ter) -> None:
        transaction = await async_client.balances.transactions.summary(
            balance_id="balanceId",
        )
        assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

    @parametrize
    async def test_raw_response_summary(self, async_client: AsyncM3ter) -> None:
        response = await async_client.balances.transactions.with_raw_response.summary(
            balance_id="balanceId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

    @parametrize
    async def test_streaming_response_summary(self, async_client: AsyncM3ter) -> None:
        async with async_client.balances.transactions.with_streaming_response.summary(
            balance_id="balanceId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionSummaryResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_summary(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `balance_id` but received ''"):
            await async_client.balances.transactions.with_raw_response.summary(
                balance_id="",
            )
