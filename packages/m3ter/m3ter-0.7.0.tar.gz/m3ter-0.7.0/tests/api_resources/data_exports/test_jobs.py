# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.data_exports import DataExportJobResponse, JobGetDownloadURLResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestJobs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        job = client.data_exports.jobs.retrieve(
            id="id",
        )
        assert_matches_type(DataExportJobResponse, job, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.data_exports.jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(DataExportJobResponse, job, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.data_exports.jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(DataExportJobResponse, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.data_exports.jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        job = client.data_exports.jobs.list()
        assert_matches_type(SyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        job = client.data_exports.jobs.list(
            date_created_end="dateCreatedEnd",
            date_created_start="dateCreatedStart",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            schedule_id="scheduleId",
            status="PENDING",
        )
        assert_matches_type(SyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.data_exports.jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(SyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.data_exports.jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(SyncCursor[DataExportJobResponse], job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_get_download_url(self, client: M3ter) -> None:
        job = client.data_exports.jobs.get_download_url(
            job_id="jobId",
        )
        assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

    @parametrize
    def test_raw_response_get_download_url(self, client: M3ter) -> None:
        response = client.data_exports.jobs.with_raw_response.get_download_url(
            job_id="jobId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = response.parse()
        assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

    @parametrize
    def test_streaming_response_get_download_url(self, client: M3ter) -> None:
        with client.data_exports.jobs.with_streaming_response.get_download_url(
            job_id="jobId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = response.parse()
            assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_get_download_url(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            client.data_exports.jobs.with_raw_response.get_download_url(
                job_id="",
            )


class TestAsyncJobs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        job = await async_client.data_exports.jobs.retrieve(
            id="id",
        )
        assert_matches_type(DataExportJobResponse, job, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.jobs.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(DataExportJobResponse, job, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.jobs.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(DataExportJobResponse, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.data_exports.jobs.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        job = await async_client.data_exports.jobs.list()
        assert_matches_type(AsyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        job = await async_client.data_exports.jobs.list(
            date_created_end="dateCreatedEnd",
            date_created_start="dateCreatedStart",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            schedule_id="scheduleId",
            status="PENDING",
        )
        assert_matches_type(AsyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.jobs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(AsyncCursor[DataExportJobResponse], job, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.jobs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(AsyncCursor[DataExportJobResponse], job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_get_download_url(self, async_client: AsyncM3ter) -> None:
        job = await async_client.data_exports.jobs.get_download_url(
            job_id="jobId",
        )
        assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

    @parametrize
    async def test_raw_response_get_download_url(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.jobs.with_raw_response.get_download_url(
            job_id="jobId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        job = await response.parse()
        assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

    @parametrize
    async def test_streaming_response_get_download_url(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.jobs.with_streaming_response.get_download_url(
            job_id="jobId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            job = await response.parse()
            assert_matches_type(JobGetDownloadURLResponse, job, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_get_download_url(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `job_id` but received ''"):
            await async_client.data_exports.jobs.with_raw_response.get_download_url(
                job_id="",
            )
