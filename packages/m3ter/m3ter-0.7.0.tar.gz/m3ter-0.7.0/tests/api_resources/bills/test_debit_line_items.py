# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.bills import (
    DebitLineItemResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDebitLineItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            debit_reason_id="debitReasonId",
            line_item_type="STANDING_CHARGE",
            reason_id="reasonId",
            version=0,
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.bills.debit_line_items.with_raw_response.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.bills.debit_line_items.with_streaming_response.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.debit_line_items.with_raw_response.create(
                bill_id="",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.retrieve(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.bills.debit_line_items.with_raw_response.retrieve(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.bills.debit_line_items.with_streaming_response.retrieve(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.debit_line_items.with_raw_response.retrieve(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.debit_line_items.with_raw_response.retrieve(
                id="",
                bill_id="billId",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            debit_reason_id="debitReasonId",
            line_item_type="STANDING_CHARGE",
            reason_id="reasonId",
            version=0,
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.bills.debit_line_items.with_raw_response.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.bills.debit_line_items.with_streaming_response.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.debit_line_items.with_raw_response.update(
                id="id",
                bill_id="",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.debit_line_items.with_raw_response.update(
                id="",
                bill_id="billId",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.list(
            bill_id="billId",
        )
        assert_matches_type(SyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.list(
            bill_id="billId",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.bills.debit_line_items.with_raw_response.list(
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = response.parse()
        assert_matches_type(SyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.bills.debit_line_items.with_streaming_response.list(
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = response.parse()
            assert_matches_type(SyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.debit_line_items.with_raw_response.list(
                bill_id="",
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        debit_line_item = client.bills.debit_line_items.delete(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.bills.debit_line_items.with_raw_response.delete(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.bills.debit_line_items.with_streaming_response.delete(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            client.bills.debit_line_items.with_raw_response.delete(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.debit_line_items.with_raw_response.delete(
                id="",
                bill_id="billId",
            )


class TestAsyncDebitLineItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            debit_reason_id="debitReasonId",
            line_item_type="STANDING_CHARGE",
            reason_id="reasonId",
            version=0,
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.debit_line_items.with_raw_response.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = await response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.debit_line_items.with_streaming_response.create(
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = await response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.create(
                bill_id="",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.retrieve(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.debit_line_items.with_raw_response.retrieve(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = await response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.debit_line_items.with_streaming_response.retrieve(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = await response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.retrieve(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.retrieve(
                id="",
                bill_id="billId",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            debit_reason_id="debitReasonId",
            line_item_type="STANDING_CHARGE",
            reason_id="reasonId",
            version=0,
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.debit_line_items.with_raw_response.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = await response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.debit_line_items.with_streaming_response.update(
            id="id",
            bill_id="billId",
            accounting_product_id="accountingProductId",
            amount=1,
            description="x",
            product_id="productId",
            referenced_bill_id="referencedBillId",
            referenced_line_item_id="referencedLineItemId",
            service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = await response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.update(
                id="id",
                bill_id="",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.update(
                id="",
                bill_id="billId",
                accounting_product_id="accountingProductId",
                amount=1,
                description="x",
                product_id="productId",
                referenced_bill_id="referencedBillId",
                referenced_line_item_id="referencedLineItemId",
                service_period_end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
                service_period_start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.list(
            bill_id="billId",
        )
        assert_matches_type(AsyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.list(
            bill_id="billId",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.debit_line_items.with_raw_response.list(
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = await response.parse()
        assert_matches_type(AsyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.debit_line_items.with_streaming_response.list(
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = await response.parse()
            assert_matches_type(AsyncCursor[DebitLineItemResponse], debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.list(
                bill_id="",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        debit_line_item = await async_client.bills.debit_line_items.delete(
            id="id",
            bill_id="billId",
        )
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.debit_line_items.with_raw_response.delete(
            id="id",
            bill_id="billId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        debit_line_item = await response.parse()
        assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.debit_line_items.with_streaming_response.delete(
            id="id",
            bill_id="billId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            debit_line_item = await response.parse()
            assert_matches_type(DebitLineItemResponse, debit_line_item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `bill_id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.delete(
                id="id",
                bill_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.debit_line_items.with_raw_response.delete(
                id="",
                bill_id="billId",
            )
