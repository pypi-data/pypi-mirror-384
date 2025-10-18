# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    UsageQueryResponse,
    DownloadURLResponse,
    SubmitMeasurementsResponse,
)
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUsage:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_get_failed_ingest_download_url(self, client: M3ter) -> None:
        usage = client.usage.get_failed_ingest_download_url()
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    def test_method_get_failed_ingest_download_url_with_all_params(self, client: M3ter) -> None:
        usage = client.usage.get_failed_ingest_download_url(
            file="file",
        )
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    def test_raw_response_get_failed_ingest_download_url(self, client: M3ter) -> None:
        response = client.usage.with_raw_response.get_failed_ingest_download_url()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = response.parse()
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    def test_streaming_response_get_failed_ingest_download_url(self, client: M3ter) -> None:
        with client.usage.with_streaming_response.get_failed_ingest_download_url() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = response.parse()
            assert_matches_type(DownloadURLResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_query(self, client: M3ter) -> None:
        usage = client.usage.query()
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    def test_method_query_with_all_params(self, client: M3ter) -> None:
        usage = client.usage.query(
            account_ids=["string"],
            aggregations=[
                {
                    "field_code": "x",
                    "field_type": "DIMENSION",
                    "function": "SUM",
                    "meter_id": "x",
                }
            ],
            dimension_filters=[
                {
                    "field_code": "x",
                    "meter_id": "x",
                    "values": ["string"],
                }
            ],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            groups=[{"group_type": "ACCOUNT"}],
            limit=1,
            meter_ids=["string"],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    def test_raw_response_query(self, client: M3ter) -> None:
        response = client.usage.with_raw_response.query()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = response.parse()
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    def test_streaming_response_query(self, client: M3ter) -> None:
        with client.usage.with_streaming_response.query() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = response.parse()
            assert_matches_type(UsageQueryResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_submit(self, client: M3ter) -> None:
        usage = client.usage.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        )
        assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

    @parametrize
    def test_method_submit_all(self, client: M3ter) -> None:
        usage = client.usage.submit_all(
            org_id="orgId",
            measurements=(
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
                for _ in range(1001)
            ),
        )

        responses = 0
        for response in usage:
            responses += 1
            assert_matches_type(SubmitMeasurementsResponse, response, path=["response"])

        assert responses == 2

    @parametrize
    def test_raw_response_submit(self, client: M3ter) -> None:
        response = client.usage.with_raw_response.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = response.parse()
        assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

    @parametrize
    def test_streaming_response_submit(self, client: M3ter) -> None:
        with client.usage.with_streaming_response.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = response.parse()
            assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUsage:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_get_failed_ingest_download_url(self, async_client: AsyncM3ter) -> None:
        usage = await async_client.usage.get_failed_ingest_download_url()
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    async def test_method_get_failed_ingest_download_url_with_all_params(self, async_client: AsyncM3ter) -> None:
        usage = await async_client.usage.get_failed_ingest_download_url(
            file="file",
        )
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    async def test_raw_response_get_failed_ingest_download_url(self, async_client: AsyncM3ter) -> None:
        response = await async_client.usage.with_raw_response.get_failed_ingest_download_url()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = await response.parse()
        assert_matches_type(DownloadURLResponse, usage, path=["response"])

    @parametrize
    async def test_streaming_response_get_failed_ingest_download_url(self, async_client: AsyncM3ter) -> None:
        async with async_client.usage.with_streaming_response.get_failed_ingest_download_url() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = await response.parse()
            assert_matches_type(DownloadURLResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_query(self, async_client: AsyncM3ter) -> None:
        usage = await async_client.usage.query()
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    async def test_method_query_with_all_params(self, async_client: AsyncM3ter) -> None:
        usage = await async_client.usage.query(
            account_ids=["string"],
            aggregations=[
                {
                    "field_code": "x",
                    "field_type": "DIMENSION",
                    "function": "SUM",
                    "meter_id": "x",
                }
            ],
            dimension_filters=[
                {
                    "field_code": "x",
                    "meter_id": "x",
                    "values": ["string"],
                }
            ],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            groups=[{"group_type": "ACCOUNT"}],
            limit=1,
            meter_ids=["string"],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    async def test_raw_response_query(self, async_client: AsyncM3ter) -> None:
        response = await async_client.usage.with_raw_response.query()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = await response.parse()
        assert_matches_type(UsageQueryResponse, usage, path=["response"])

    @parametrize
    async def test_streaming_response_query(self, async_client: AsyncM3ter) -> None:
        async with async_client.usage.with_streaming_response.query() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = await response.parse()
            assert_matches_type(UsageQueryResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_submit(self, async_client: AsyncM3ter) -> None:
        usage = await async_client.usage.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        )
        assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

    @parametrize
    async def test_method_submit_all(self, async_client: AsyncM3ter) -> None:
        usage = async_client.usage.submit_all(
            org_id="orgId",
            measurements=(
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
                for _ in range(1001)
            ),
        )

        responses = 0
        async for response in usage:
            responses += 1
            assert_matches_type(SubmitMeasurementsResponse, response, path=["response"])

        assert responses == 2

    @parametrize
    async def test_raw_response_submit(self, async_client: AsyncM3ter) -> None:
        response = await async_client.usage.with_raw_response.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        usage = await response.parse()
        assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

    @parametrize
    async def test_streaming_response_submit(self, async_client: AsyncM3ter) -> None:
        async with async_client.usage.with_streaming_response.submit(
            measurements=[
                {
                    "account": "Acme Corp",
                    "meter": "string",
                    "ts": parse_datetime("2022-08-24T14:15:22Z"),
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            usage = await response.parse()
            assert_matches_type(SubmitMeasurementsResponse, usage, path=["response"])

        assert cast(Any, response.is_closed) is True
