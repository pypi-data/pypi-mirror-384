# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import OrganizationConfigResponse
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOrganizationConfig:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        organization_config = client.organization_config.retrieve()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.organization_config.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization_config = response.parse()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.organization_config.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization_config = response.parse()
            assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        organization_config = client.organization_config.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        )
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        organization_config = client.organization_config.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
            auto_approve_bills_grace_period=2,
            auto_approve_bills_grace_period_unit="DAYS",
            auto_generate_statement_mode="NONE",
            bill_prefix="Bill-",
            commitment_fee_bill_in_advance=True,
            consolidate_bills=True,
            credit_application_order=["PREPAYMENT"],
            currency_conversions=[
                {
                    "from": "EUR",
                    "to": "USD",
                    "multiplier": 1.12,
                }
            ],
            default_statement_definition_id="defaultStatementDefinitionId",
            external_invoice_date="LAST_DAY_OF_ARREARS",
            minimum_spend_bill_in_advance=True,
            scheduled_bill_interval=0,
            sequence_start_number=1000,
            standing_charge_bill_in_advance=True,
            suppressed_empty_bills=True,
            version=0,
        )
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.organization_config.with_raw_response.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization_config = response.parse()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.organization_config.with_streaming_response.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization_config = response.parse()
            assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncOrganizationConfig:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        organization_config = await async_client.organization_config.retrieve()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.organization_config.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization_config = await response.parse()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.organization_config.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization_config = await response.parse()
            assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        organization_config = await async_client.organization_config.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        )
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        organization_config = await async_client.organization_config.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
            auto_approve_bills_grace_period=2,
            auto_approve_bills_grace_period_unit="DAYS",
            auto_generate_statement_mode="NONE",
            bill_prefix="Bill-",
            commitment_fee_bill_in_advance=True,
            consolidate_bills=True,
            credit_application_order=["PREPAYMENT"],
            currency_conversions=[
                {
                    "from": "EUR",
                    "to": "USD",
                    "multiplier": 1.12,
                }
            ],
            default_statement_definition_id="defaultStatementDefinitionId",
            external_invoice_date="LAST_DAY_OF_ARREARS",
            minimum_spend_bill_in_advance=True,
            scheduled_bill_interval=0,
            sequence_start_number=1000,
            standing_charge_bill_in_advance=True,
            suppressed_empty_bills=True,
            version=0,
        )
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.organization_config.with_raw_response.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        organization_config = await response.parse()
        assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.organization_config.with_streaming_response.update(
            currency="USD",
            day_epoch="2022-01-01",
            days_before_bill_due=1,
            month_epoch="2022-01-01",
            timezone="UTC",
            week_epoch="2022-01-04",
            year_epoch="2022-01-01",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            organization_config = await response.parse()
            assert_matches_type(OrganizationConfigResponse, organization_config, path=["response"])

        assert cast(Any, response.is_closed) is True
