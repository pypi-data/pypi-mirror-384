# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    CounterPricingResponse,
)
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCounterPricings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            code='S?oC"$]C] ]]]]]5]',
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_id="planId",
            plan_template_id="planTemplateId",
            pro_rate_adjustment_credit=True,
            pro_rate_adjustment_debit=True,
            pro_rate_running_total=True,
            running_total_bill_in_advance=True,
            version=0,
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.counter_pricings.with_raw_response.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.counter_pricings.with_streaming_response.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.retrieve(
            id="id",
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.counter_pricings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.counter_pricings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counter_pricings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            code='S?oC"$]C] ]]]]]5]',
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_id="planId",
            plan_template_id="planTemplateId",
            pro_rate_adjustment_credit=True,
            pro_rate_adjustment_debit=True,
            pro_rate_running_total=True,
            running_total_bill_in_advance=True,
            version=0,
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.counter_pricings.with_raw_response.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.counter_pricings.with_streaming_response.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counter_pricings.with_raw_response.update(
                id="",
                counter_id="x",
                pricing_bands=[
                    {
                        "fixed_price": 0,
                        "lower_limit": 0,
                        "unit_price": 0,
                    }
                ],
                start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.list()
        assert_matches_type(SyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.list(
            date="date",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            plan_id="planId",
            plan_template_id="planTemplateId",
        )
        assert_matches_type(SyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.counter_pricings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = response.parse()
        assert_matches_type(SyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.counter_pricings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = response.parse()
            assert_matches_type(SyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        counter_pricing = client.counter_pricings.delete(
            id="id",
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.counter_pricings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.counter_pricings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.counter_pricings.with_raw_response.delete(
                id="",
            )


class TestAsyncCounterPricings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            code='S?oC"$]C] ]]]]]5]',
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_id="planId",
            plan_template_id="planTemplateId",
            pro_rate_adjustment_credit=True,
            pro_rate_adjustment_debit=True,
            pro_rate_running_total=True,
            running_total_bill_in_advance=True,
            version=0,
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counter_pricings.with_raw_response.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = await response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.counter_pricings.with_streaming_response.create(
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = await response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.retrieve(
            id="id",
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counter_pricings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = await response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.counter_pricings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = await response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counter_pricings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            accounting_product_id="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            code='S?oC"$]C] ]]]]]5]',
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            plan_id="planId",
            plan_template_id="planTemplateId",
            pro_rate_adjustment_credit=True,
            pro_rate_adjustment_debit=True,
            pro_rate_running_total=True,
            running_total_bill_in_advance=True,
            version=0,
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counter_pricings.with_raw_response.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = await response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.counter_pricings.with_streaming_response.update(
            id="id",
            counter_id="x",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = await response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counter_pricings.with_raw_response.update(
                id="",
                counter_id="x",
                pricing_bands=[
                    {
                        "fixed_price": 0,
                        "lower_limit": 0,
                        "unit_price": 0,
                    }
                ],
                start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.list()
        assert_matches_type(AsyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.list(
            date="date",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            plan_id="planId",
            plan_template_id="planTemplateId",
        )
        assert_matches_type(AsyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counter_pricings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = await response.parse()
        assert_matches_type(AsyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.counter_pricings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = await response.parse()
            assert_matches_type(AsyncCursor[CounterPricingResponse], counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        counter_pricing = await async_client.counter_pricings.delete(
            id="id",
        )
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.counter_pricings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        counter_pricing = await response.parse()
        assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.counter_pricings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            counter_pricing = await response.parse()
            assert_matches_type(CounterPricingResponse, counter_pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.counter_pricings.with_raw_response.delete(
                id="",
            )
