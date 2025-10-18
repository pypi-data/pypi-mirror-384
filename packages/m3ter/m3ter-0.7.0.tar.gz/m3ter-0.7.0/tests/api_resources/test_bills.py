# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    BillResponse,
    BillSearchResponse,
    BillApproveResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBills:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        bill = client.bills.retrieve(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_method_retrieve_with_all_params(self, client: M3ter) -> None:
        bill = client.bills.retrieve(
            id="id",
            additional=["string"],
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        bill = client.bills.list()
        assert_matches_type(SyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        bill = client.bills.list(
            account_id="accountId",
            additional=["string"],
            bill_date="billDate",
            bill_date_end="billDateEnd",
            bill_date_start="billDateStart",
            billing_frequency="billingFrequency",
            exclude_line_items=True,
            external_invoice_date_end="externalInvoiceDateEnd",
            external_invoice_date_start="externalInvoiceDateStart",
            ids=["string"],
            include_bill_total=True,
            locked=True,
            next_token="nextToken",
            page_size=1,
            status="PENDING",
        )
        assert_matches_type(SyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(SyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(SyncCursor[BillResponse], bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        bill = client.bills.delete(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.with_raw_response.delete(
                id="",
            )

    @parametrize
    def test_method_approve(self, client: M3ter) -> None:
        bill = client.bills.approve(
            bill_ids=["string"],
        )
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    def test_method_approve_with_all_params(self, client: M3ter) -> None:
        bill = client.bills.approve(
            bill_ids=["string"],
            account_ids="accountIds",
            external_invoice_date_end="externalInvoiceDateEnd",
            external_invoice_date_start="externalInvoiceDateStart",
        )
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_approve(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.approve(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_approve(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.approve(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillApproveResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_latest_by_account(self, client: M3ter) -> None:
        bill = client.bills.latest_by_account(
            account_id="accountId",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_method_latest_by_account_with_all_params(self, client: M3ter) -> None:
        bill = client.bills.latest_by_account(
            account_id="accountId",
            additional=["string"],
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_latest_by_account(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.latest_by_account(
            account_id="accountId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_latest_by_account(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.latest_by_account(
            account_id="accountId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_latest_by_account(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.bills.with_raw_response.latest_by_account(
                account_id="",
            )

    @parametrize
    def test_method_lock(self, client: M3ter) -> None:
        bill = client.bills.lock(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_lock(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.lock(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_lock(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.lock(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_lock(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.with_raw_response.lock(
                id="",
            )

    @parametrize
    def test_method_search(self, client: M3ter) -> None:
        bill = client.bills.search()
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    def test_method_search_with_all_params(self, client: M3ter) -> None:
        bill = client.bills.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_search(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_search(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillSearchResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_update_status(self, client: M3ter) -> None:
        bill = client.bills.update_status(
            id="id",
            status="PENDING",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_raw_response_update_status(self, client: M3ter) -> None:
        response = client.bills.with_raw_response.update_status(
            id="id",
            status="PENDING",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    def test_streaming_response_update_status(self, client: M3ter) -> None:
        with client.bills.with_streaming_response.update_status(
            id="id",
            status="PENDING",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_status(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bills.with_raw_response.update_status(
                id="",
                status="PENDING",
            )


class TestAsyncBills:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.retrieve(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.retrieve(
            id="id",
            additional=["string"],
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.list()
        assert_matches_type(AsyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.list(
            account_id="accountId",
            additional=["string"],
            bill_date="billDate",
            bill_date_end="billDateEnd",
            bill_date_start="billDateStart",
            billing_frequency="billingFrequency",
            exclude_line_items=True,
            external_invoice_date_end="externalInvoiceDateEnd",
            external_invoice_date_start="externalInvoiceDateStart",
            ids=["string"],
            include_bill_total=True,
            locked=True,
            next_token="nextToken",
            page_size=1,
            status="PENDING",
        )
        assert_matches_type(AsyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(AsyncCursor[BillResponse], bill, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(AsyncCursor[BillResponse], bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.delete(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.with_raw_response.delete(
                id="",
            )

    @parametrize
    async def test_method_approve(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.approve(
            bill_ids=["string"],
        )
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    async def test_method_approve_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.approve(
            bill_ids=["string"],
            account_ids="accountIds",
            external_invoice_date_end="externalInvoiceDateEnd",
            external_invoice_date_start="externalInvoiceDateStart",
        )
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_approve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.approve(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillApproveResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_approve(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.approve(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillApproveResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_latest_by_account(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.latest_by_account(
            account_id="accountId",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_method_latest_by_account_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.latest_by_account(
            account_id="accountId",
            additional=["string"],
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_latest_by_account(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.latest_by_account(
            account_id="accountId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_latest_by_account(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.latest_by_account(
            account_id="accountId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_latest_by_account(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.bills.with_raw_response.latest_by_account(
                account_id="",
            )

    @parametrize
    async def test_method_lock(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.lock(
            id="id",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_lock(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.lock(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_lock(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.lock(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_lock(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.with_raw_response.lock(
                id="",
            )

    @parametrize
    async def test_method_search(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.search()
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_search(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillSearchResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillSearchResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_update_status(self, async_client: AsyncM3ter) -> None:
        bill = await async_client.bills.update_status(
            id="id",
            status="PENDING",
        )
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_raw_response_update_status(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bills.with_raw_response.update_status(
            id="id",
            status="PENDING",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill = await response.parse()
        assert_matches_type(BillResponse, bill, path=["response"])

    @parametrize
    async def test_streaming_response_update_status(self, async_client: AsyncM3ter) -> None:
        async with async_client.bills.with_streaming_response.update_status(
            id="id",
            status="PENDING",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill = await response.parse()
            assert_matches_type(BillResponse, bill, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_status(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bills.with_raw_response.update_status(
                id="",
                status="PENDING",
            )
