# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    CommitmentResponse,
    CommitmentSearchResponse,
)
from tests.utils import assert_matches_type
from m3ter._utils import parse_date, parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCommitments:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        commitment = client.commitments.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        commitment = client.commitments.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount_first_bill=0,
            amount_pre_paid=0,
            bill_epoch=parse_date("2019-12-27"),
            billing_interval=1,
            billing_offset=0,
            billing_plan_id="billingPlanId",
            child_billing_mode="PARENT_SUMMARY",
            commitment_fee_bill_in_advance=True,
            commitment_fee_description="commitmentFeeDescription",
            commitment_usage_description="commitmentUsageDescription",
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            drawdowns_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            fee_dates=[
                {
                    "amount": 1,
                    "date": parse_date("2019-12-27"),
                    "service_period_end_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "service_period_start_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                }
            ],
            fees_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            line_item_types=["STANDING_CHARGE"],
            overage_description="overageDescription",
            overage_surcharge_percent=0,
            product_ids=["string"],
            separate_overage_usage=True,
            version=0,
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        commitment = client.commitments.retrieve(
            id="id",
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.commitments.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        commitment = client.commitments.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        commitment = client.commitments.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount_first_bill=0,
            amount_pre_paid=0,
            bill_epoch=parse_date("2019-12-27"),
            billing_interval=1,
            billing_offset=0,
            billing_plan_id="billingPlanId",
            child_billing_mode="PARENT_SUMMARY",
            commitment_fee_bill_in_advance=True,
            commitment_fee_description="commitmentFeeDescription",
            commitment_usage_description="commitmentUsageDescription",
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            drawdowns_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            fee_dates=[
                {
                    "amount": 1,
                    "date": parse_date("2019-12-27"),
                    "service_period_end_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "service_period_start_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                }
            ],
            fees_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            line_item_types=["STANDING_CHARGE"],
            overage_description="overageDescription",
            overage_surcharge_percent=0,
            product_ids=["string"],
            separate_overage_usage=True,
            version=0,
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.commitments.with_raw_response.update(
                id="",
                account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                amount=1,
                currency="x",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        commitment = client.commitments.list()
        assert_matches_type(SyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        commitment = client.commitments.list(
            account_id="accountId",
            contract_id="contractId",
            date="date",
            end_date_end="endDateEnd",
            end_date_start="endDateStart",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            product_id="productId",
        )
        assert_matches_type(SyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(SyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(SyncCursor[CommitmentResponse], commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        commitment = client.commitments.delete(
            id="id",
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.commitments.with_raw_response.delete(
                id="",
            )

    @parametrize
    def test_method_search(self, client: M3ter) -> None:
        commitment = client.commitments.search()
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    def test_method_search_with_all_params(self, client: M3ter) -> None:
        commitment = client.commitments.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    def test_raw_response_search(self, client: M3ter) -> None:
        response = client.commitments.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = response.parse()
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    def test_streaming_response_search(self, client: M3ter) -> None:
        with client.commitments.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = response.parse()
            assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCommitments:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount_first_bill=0,
            amount_pre_paid=0,
            bill_epoch=parse_date("2019-12-27"),
            billing_interval=1,
            billing_offset=0,
            billing_plan_id="billingPlanId",
            child_billing_mode="PARENT_SUMMARY",
            commitment_fee_bill_in_advance=True,
            commitment_fee_description="commitmentFeeDescription",
            commitment_usage_description="commitmentUsageDescription",
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            drawdowns_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            fee_dates=[
                {
                    "amount": 1,
                    "date": parse_date("2019-12-27"),
                    "service_period_end_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "service_period_start_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                }
            ],
            fees_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            line_item_types=["STANDING_CHARGE"],
            overage_description="overageDescription",
            overage_surcharge_percent=0,
            product_ids=["string"],
            separate_overage_usage=True,
            version=0,
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.create(
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.retrieve(
            id="id",
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.commitments.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount_first_bill=0,
            amount_pre_paid=0,
            bill_epoch=parse_date("2019-12-27"),
            billing_interval=1,
            billing_offset=0,
            billing_plan_id="billingPlanId",
            child_billing_mode="PARENT_SUMMARY",
            commitment_fee_bill_in_advance=True,
            commitment_fee_description="commitmentFeeDescription",
            commitment_usage_description="commitmentUsageDescription",
            contract_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            drawdowns_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            fee_dates=[
                {
                    "amount": 1,
                    "date": parse_date("2019-12-27"),
                    "service_period_end_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                    "service_period_start_date": parse_datetime("2019-12-27T18:11:19.117Z"),
                }
            ],
            fees_accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            line_item_types=["STANDING_CHARGE"],
            overage_description="overageDescription",
            overage_surcharge_percent=0,
            product_ids=["string"],
            separate_overage_usage=True,
            version=0,
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.update(
            id="id",
            account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            amount=1,
            currency="x",
            end_date=parse_date("2019-12-27"),
            start_date=parse_date("2019-12-27"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.commitments.with_raw_response.update(
                id="",
                account_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                amount=1,
                currency="x",
                end_date=parse_date("2019-12-27"),
                start_date=parse_date("2019-12-27"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.list()
        assert_matches_type(AsyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.list(
            account_id="accountId",
            contract_id="contractId",
            date="date",
            end_date_end="endDateEnd",
            end_date_start="endDateStart",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            product_id="productId",
        )
        assert_matches_type(AsyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(AsyncCursor[CommitmentResponse], commitment, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(AsyncCursor[CommitmentResponse], commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.delete(
            id="id",
        )
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(CommitmentResponse, commitment, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(CommitmentResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.commitments.with_raw_response.delete(
                id="",
            )

    @parametrize
    async def test_method_search(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.search()
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncM3ter) -> None:
        commitment = await async_client.commitments.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    async def test_raw_response_search(self, async_client: AsyncM3ter) -> None:
        response = await async_client.commitments.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        commitment = await response.parse()
        assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncM3ter) -> None:
        async with async_client.commitments.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            commitment = await response.parse()
            assert_matches_type(CommitmentSearchResponse, commitment, path=["response"])

        assert cast(Any, response.is_closed) is True
