# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import BillJobResponse
from tests.utils import assert_matches_type
from m3ter._utils import parse_date
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBillJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.create()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.create(
            account_ids=["string"],
            bill_date=parse_date("2019-12-27"),
            bill_frequency_interval=0,
            billing_frequency="DAILY",
            currency_conversions=[
                {
                    "from": "EUR",
                    "to": "USD",
                    "multiplier": 1.12,
                }
            ],
            day_epoch=parse_date("2019-12-27"),
            due_date=parse_date("2019-12-27"),
            external_invoice_date=parse_date("2019-12-27"),
            last_date_in_billing_period=parse_date("2019-12-27"),
            month_epoch=parse_date("2019-12-27"),
            target_currency="xxx",
            timezone="UTC",
            version=0,
            week_epoch=parse_date("2019-12-27"),
            year_epoch=parse_date("2019-12-27"),
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.bill_jobs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.bill_jobs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.retrieve(
            id="id",
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.bill_jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.bill_jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bill_jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.list()
        assert_matches_type(SyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.list(
            active="active",
            next_token="nextToken",
            page_size=1,
            status="status",
        )
        assert_matches_type(SyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.bill_jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = response.parse()
        assert_matches_type(SyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.bill_jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = response.parse()
            assert_matches_type(SyncCursor[BillJobResponse], bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_cancel(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.cancel(
            id="id",
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_raw_response_cancel(self, client: M3ter) -> None:
        response = client.bill_jobs.with_raw_response.cancel(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_streaming_response_cancel(self, client: M3ter) -> None:
        with client.bill_jobs.with_streaming_response.cancel(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_cancel(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.bill_jobs.with_raw_response.cancel(
                id="",
            )

    @parametrize
    def test_method_recalculate(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.recalculate(
            bill_ids=["string"],
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_method_recalculate_with_all_params(self, client: M3ter) -> None:
        bill_job = client.bill_jobs.recalculate(
            bill_ids=["string"],
            version=0,
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_raw_response_recalculate(self, client: M3ter) -> None:
        response = client.bill_jobs.with_raw_response.recalculate(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    def test_streaming_response_recalculate(self, client: M3ter) -> None:
        with client.bill_jobs.with_streaming_response.recalculate(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncBillJobs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.create()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.create(
            account_ids=["string"],
            bill_date=parse_date("2019-12-27"),
            bill_frequency_interval=0,
            billing_frequency="DAILY",
            currency_conversions=[
                {
                    "from": "EUR",
                    "to": "USD",
                    "multiplier": 1.12,
                }
            ],
            day_epoch=parse_date("2019-12-27"),
            due_date=parse_date("2019-12-27"),
            external_invoice_date=parse_date("2019-12-27"),
            last_date_in_billing_period=parse_date("2019-12-27"),
            month_epoch=parse_date("2019-12-27"),
            target_currency="xxx",
            timezone="UTC",
            version=0,
            week_epoch=parse_date("2019-12-27"),
            year_epoch=parse_date("2019-12-27"),
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bill_jobs.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = await response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.bill_jobs.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = await response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.retrieve(
            id="id",
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bill_jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = await response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.bill_jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = await response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bill_jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.list()
        assert_matches_type(AsyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.list(
            active="active",
            next_token="nextToken",
            page_size=1,
            status="status",
        )
        assert_matches_type(AsyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bill_jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = await response.parse()
        assert_matches_type(AsyncCursor[BillJobResponse], bill_job, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.bill_jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = await response.parse()
            assert_matches_type(AsyncCursor[BillJobResponse], bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_cancel(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.cancel(
            id="id",
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bill_jobs.with_raw_response.cancel(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = await response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncM3ter) -> None:
        async with async_client.bill_jobs.with_streaming_response.cancel(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = await response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.bill_jobs.with_raw_response.cancel(
                id="",
            )

    @parametrize
    async def test_method_recalculate(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.recalculate(
            bill_ids=["string"],
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_method_recalculate_with_all_params(self, async_client: AsyncM3ter) -> None:
        bill_job = await async_client.bill_jobs.recalculate(
            bill_ids=["string"],
            version=0,
        )
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_raw_response_recalculate(self, async_client: AsyncM3ter) -> None:
        response = await async_client.bill_jobs.with_raw_response.recalculate(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        bill_job = await response.parse()
        assert_matches_type(BillJobResponse, bill_job, path=["response"])

    @parametrize
    async def test_streaming_response_recalculate(self, async_client: AsyncM3ter) -> None:
        async with async_client.bill_jobs.with_streaming_response.recalculate(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            bill_job = await response.parse()
            assert_matches_type(BillJobResponse, bill_job, path=["response"])

        assert cast(Any, response.is_closed) is True
