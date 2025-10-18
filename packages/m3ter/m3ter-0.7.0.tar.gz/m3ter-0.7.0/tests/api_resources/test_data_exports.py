# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import AdHocResponse
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDataExports:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_adhoc_overload_1(self, client: M3ter) -> None:
        data_export = client.data_exports.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_method_create_adhoc_with_all_params_overload_1(self, client: M3ter) -> None:
        data_export = client.data_exports.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
            version=0,
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_raw_response_create_adhoc_overload_1(self, client: M3ter) -> None:
        response = client.data_exports.with_raw_response.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data_export = response.parse()
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_streaming_response_create_adhoc_overload_1(self, client: M3ter) -> None:
        with client.data_exports.with_streaming_response.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data_export = response.parse()
            assert_matches_type(AdHocResponse, data_export, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_adhoc_overload_2(self, client: M3ter) -> None:
        data_export = client.data_exports.create_adhoc(
            source_type="USAGE",
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_method_create_adhoc_with_all_params_overload_2(self, client: M3ter) -> None:
        data_export = client.data_exports.create_adhoc(
            source_type="USAGE",
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
            meter_ids=["string"],
            version=0,
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_raw_response_create_adhoc_overload_2(self, client: M3ter) -> None:
        response = client.data_exports.with_raw_response.create_adhoc(
            source_type="USAGE",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data_export = response.parse()
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    def test_streaming_response_create_adhoc_overload_2(self, client: M3ter) -> None:
        with client.data_exports.with_streaming_response.create_adhoc(
            source_type="USAGE",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data_export = response.parse()
            assert_matches_type(AdHocResponse, data_export, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncDataExports:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_adhoc_overload_1(self, async_client: AsyncM3ter) -> None:
        data_export = await async_client.data_exports.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_method_create_adhoc_with_all_params_overload_1(self, async_client: AsyncM3ter) -> None:
        data_export = await async_client.data_exports.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
            version=0,
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_raw_response_create_adhoc_overload_1(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.with_raw_response.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data_export = await response.parse()
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_streaming_response_create_adhoc_overload_1(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.with_streaming_response.create_adhoc(
            operational_data_types=["BILLS"],
            source_type="OPERATIONAL",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data_export = await response.parse()
            assert_matches_type(AdHocResponse, data_export, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_adhoc_overload_2(self, async_client: AsyncM3ter) -> None:
        data_export = await async_client.data_exports.create_adhoc(
            source_type="USAGE",
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_method_create_adhoc_with_all_params_overload_2(self, async_client: AsyncM3ter) -> None:
        data_export = await async_client.data_exports.create_adhoc(
            source_type="USAGE",
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
            meter_ids=["string"],
            version=0,
        )
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_raw_response_create_adhoc_overload_2(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.with_raw_response.create_adhoc(
            source_type="USAGE",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        data_export = await response.parse()
        assert_matches_type(AdHocResponse, data_export, path=["response"])

    @parametrize
    async def test_streaming_response_create_adhoc_overload_2(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.with_streaming_response.create_adhoc(
            source_type="USAGE",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            data_export = await response.parse()
            assert_matches_type(AdHocResponse, data_export, path=["response"])

        assert cast(Any, response.is_closed) is True
