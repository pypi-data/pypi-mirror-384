# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import PricingResponse
from tests.utils import assert_matches_type
from m3ter._utils import parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPricings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        pricing = client.pricings.create(
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        pricing = client.pricings.create(
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
            aggregation_id="aggregationId",
            code='S?oC"$]C] ]]]]]5]',
            compound_aggregation_id="compoundAggregationId",
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            minimum_spend=0,
            minimum_spend_bill_in_advance=True,
            minimum_spend_description="minimumSpendDescription",
            overage_pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            plan_id="planId",
            plan_template_id="planTemplateId",
            segment={"foo": "string"},
            tiers_span_plan=True,
            type="DEBIT",
            version=0,
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.pricings.with_raw_response.create(
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
        pricing = response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.pricings.with_streaming_response.create(
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

            pricing = response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        pricing = client.pricings.retrieve(
            id="id",
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.pricings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.pricings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.pricings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        pricing = client.pricings.update(
            id="id",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        pricing = client.pricings.update(
            id="id",
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
            aggregation_id="aggregationId",
            code='S?oC"$]C] ]]]]]5]',
            compound_aggregation_id="compoundAggregationId",
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            minimum_spend=0,
            minimum_spend_bill_in_advance=True,
            minimum_spend_description="minimumSpendDescription",
            overage_pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            plan_id="planId",
            plan_template_id="planTemplateId",
            segment={"foo": "string"},
            tiers_span_plan=True,
            type="DEBIT",
            version=0,
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.pricings.with_raw_response.update(
            id="id",
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
        pricing = response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.pricings.with_streaming_response.update(
            id="id",
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

            pricing = response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.pricings.with_raw_response.update(
                id="",
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
        pricing = client.pricings.list()
        assert_matches_type(SyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        pricing = client.pricings.list(
            aggregation_id="aggregationId",
            date="date",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            plan_id="planId",
            plan_template_id="planTemplateId",
        )
        assert_matches_type(SyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.pricings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = response.parse()
        assert_matches_type(SyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.pricings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = response.parse()
            assert_matches_type(SyncCursor[PricingResponse], pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        pricing = client.pricings.delete(
            id="id",
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.pricings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.pricings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.pricings.with_raw_response.delete(
                id="",
            )


class TestAsyncPricings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.create(
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.create(
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
            aggregation_id="aggregationId",
            code='S?oC"$]C] ]]]]]5]',
            compound_aggregation_id="compoundAggregationId",
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            minimum_spend=0,
            minimum_spend_bill_in_advance=True,
            minimum_spend_description="minimumSpendDescription",
            overage_pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            plan_id="planId",
            plan_template_id="planTemplateId",
            segment={"foo": "string"},
            tiers_span_plan=True,
            type="DEBIT",
            version=0,
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.pricings.with_raw_response.create(
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
        pricing = await response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.pricings.with_streaming_response.create(
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

            pricing = await response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.retrieve(
            id="id",
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.pricings.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = await response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.pricings.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = await response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.pricings.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.update(
            id="id",
            pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                }
            ],
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.update(
            id="id",
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
            aggregation_id="aggregationId",
            code='S?oC"$]C] ]]]]]5]',
            compound_aggregation_id="compoundAggregationId",
            cumulative=True,
            description="description",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            minimum_spend=0,
            minimum_spend_bill_in_advance=True,
            minimum_spend_description="minimumSpendDescription",
            overage_pricing_bands=[
                {
                    "fixed_price": 0,
                    "lower_limit": 0,
                    "unit_price": 0,
                    "id": "id",
                    "credit_type_id": "creditTypeId",
                }
            ],
            plan_id="planId",
            plan_template_id="planTemplateId",
            segment={"foo": "string"},
            tiers_span_plan=True,
            type="DEBIT",
            version=0,
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.pricings.with_raw_response.update(
            id="id",
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
        pricing = await response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.pricings.with_streaming_response.update(
            id="id",
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

            pricing = await response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.pricings.with_raw_response.update(
                id="",
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
        pricing = await async_client.pricings.list()
        assert_matches_type(AsyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.list(
            aggregation_id="aggregationId",
            date="date",
            ids=["string"],
            next_token="nextToken",
            page_size=1,
            plan_id="planId",
            plan_template_id="planTemplateId",
        )
        assert_matches_type(AsyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.pricings.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = await response.parse()
        assert_matches_type(AsyncCursor[PricingResponse], pricing, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.pricings.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = await response.parse()
            assert_matches_type(AsyncCursor[PricingResponse], pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        pricing = await async_client.pricings.delete(
            id="id",
        )
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.pricings.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pricing = await response.parse()
        assert_matches_type(PricingResponse, pricing, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.pricings.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pricing = await response.parse()
            assert_matches_type(PricingResponse, pricing, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.pricings.with_raw_response.delete(
                id="",
            )
