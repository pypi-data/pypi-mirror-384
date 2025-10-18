# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.statements import (
    StatementJobResponse,
    StatementJobCreateBatchResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStatementJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.create(
            bill_id="x",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.create(
            bill_id="x",
            include_csv_format=True,
            version=0,
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.statements.statement_jobs.with_raw_response.create(
            bill_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.statements.statement_jobs.with_streaming_response.create(
            bill_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.retrieve(
            id="id",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.statements.statement_jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.statements.statement_jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.statement_jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.list()
        assert_matches_type(SyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.list(
            active="active",
            bill_id="billId",
            next_token="nextToken",
            page_size=1,
            status="status",
        )
        assert_matches_type(SyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.statements.statement_jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = response.parse()
        assert_matches_type(SyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.statements.statement_jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = response.parse()
            assert_matches_type(SyncCursor[StatementJobResponse], statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_cancel(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.cancel(
            id="id",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_raw_response_cancel(self, client: M3ter) -> None:
        response = client.statements.statement_jobs.with_raw_response.cancel(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    def test_streaming_response_cancel(self, client: M3ter) -> None:
        with client.statements.statement_jobs.with_streaming_response.cancel(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_cancel(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.statements.statement_jobs.with_raw_response.cancel(
                id="",
            )

    @parametrize
    def test_method_create_batch(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.create_batch(
            bill_ids=["string"],
        )
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    def test_method_create_batch_with_all_params(self, client: M3ter) -> None:
        statement_job = client.statements.statement_jobs.create_batch(
            bill_ids=["string"],
            include_csv_format=True,
            version=0,
        )
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    def test_raw_response_create_batch(self, client: M3ter) -> None:
        response = client.statements.statement_jobs.with_raw_response.create_batch(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = response.parse()
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    def test_streaming_response_create_batch(self, client: M3ter) -> None:
        with client.statements.statement_jobs.with_streaming_response.create_batch(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = response.parse()
            assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncStatementJobs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.create(
            bill_id="x",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.create(
            bill_id="x",
            include_csv_format=True,
            version=0,
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_jobs.with_raw_response.create(
            bill_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = await response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_jobs.with_streaming_response.create(
            bill_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = await response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.retrieve(
            id="id",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = await response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = await response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.statement_jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.list()
        assert_matches_type(AsyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.list(
            active="active",
            bill_id="billId",
            next_token="nextToken",
            page_size=1,
            status="status",
        )
        assert_matches_type(AsyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = await response.parse()
        assert_matches_type(AsyncCursor[StatementJobResponse], statement_job, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = await response.parse()
            assert_matches_type(AsyncCursor[StatementJobResponse], statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_cancel(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.cancel(
            id="id",
        )
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_jobs.with_raw_response.cancel(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = await response.parse()
        assert_matches_type(StatementJobResponse, statement_job, path=["response"])

    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_jobs.with_streaming_response.cancel(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = await response.parse()
            assert_matches_type(StatementJobResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.statements.statement_jobs.with_raw_response.cancel(
                id="",
            )

    @parametrize
    async def test_method_create_batch(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.create_batch(
            bill_ids=["string"],
        )
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    async def test_method_create_batch_with_all_params(self, async_client: AsyncM3ter) -> None:
        statement_job = await async_client.statements.statement_jobs.create_batch(
            bill_ids=["string"],
            include_csv_format=True,
            version=0,
        )
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    async def test_raw_response_create_batch(self, async_client: AsyncM3ter) -> None:
        response = await async_client.statements.statement_jobs.with_raw_response.create_batch(
            bill_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement_job = await response.parse()
        assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

    @parametrize
    async def test_streaming_response_create_batch(self, async_client: AsyncM3ter) -> None:
        async with async_client.statements.statement_jobs.with_streaming_response.create_batch(
            bill_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement_job = await response.parse()
            assert_matches_type(StatementJobCreateBatchResponse, statement_job, path=["response"])

        assert cast(Any, response.is_closed) is True
