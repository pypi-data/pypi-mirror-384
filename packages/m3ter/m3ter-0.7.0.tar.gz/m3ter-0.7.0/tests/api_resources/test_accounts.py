# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    AccountResponse,
    AccountSearchResponse,
    AccountEndDateBillingEntitiesResponse,
)
from tests.utils import assert_matches_type
from m3ter._utils import parse_date, parse_datetime
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAccounts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        account = client.accounts.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
            address={
                "address_line1": "addressLine1",
                "address_line2": "addressLine2",
                "address_line3": "addressLine3",
                "address_line4": "addressLine4",
                "country": "country",
                "locality": "locality",
                "post_code": "postCode",
                "region": "region",
            },
            auto_generate_statement_mode="NONE",
            bill_epoch=parse_date("2019-12-27"),
            config_data={"foo": "bar"},
            credit_application_order=["PREPAYMENT"],
            currency="USD",
            custom_fields={"foo": "string"},
            days_before_bill_due=1,
            parent_account_id="parentAccountId",
            purchase_order_number="purchaseOrderNumber",
            statement_definition_id="statementDefinitionId",
            version=0,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        account = client.accounts.retrieve(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.accounts.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        account = client.accounts.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
            address={
                "address_line1": "addressLine1",
                "address_line2": "addressLine2",
                "address_line3": "addressLine3",
                "address_line4": "addressLine4",
                "country": "country",
                "locality": "locality",
                "post_code": "postCode",
                "region": "region",
            },
            auto_generate_statement_mode="NONE",
            bill_epoch=parse_date("2019-12-27"),
            config_data={"foo": "bar"},
            credit_application_order=["PREPAYMENT"],
            currency="USD",
            custom_fields={"foo": "string"},
            days_before_bill_due=1,
            parent_account_id="parentAccountId",
            purchase_order_number="purchaseOrderNumber",
            statement_definition_id="statementDefinitionId",
            version=0,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.accounts.with_raw_response.update(
                id="",
                code='S?oC"$]C] ]]]]]5]',
                email_address="dev@stainless.com",
                name="x",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        account = client.accounts.list()
        assert_matches_type(SyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.list(
            codes=["string"],
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(SyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(SyncCursor[AccountResponse], account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        account = client.accounts.delete(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.accounts.with_raw_response.delete(
                id="",
            )

    @parametrize
    def test_method_end_date_billing_entities(self, client: M3ter) -> None:
        account = client.accounts.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    def test_method_end_date_billing_entities_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            apply_to_children=True,
        )
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    def test_raw_response_end_date_billing_entities(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_end_date_billing_entities(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_end_date_billing_entities(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.accounts.with_raw_response.end_date_billing_entities(
                id="",
                billing_entities=["CONTRACT"],
                end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    def test_method_get_children(self, client: M3ter) -> None:
        account = client.accounts.get_children(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_method_get_children_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.get_children(
            id="id",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_raw_response_get_children(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.get_children(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_get_children(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.get_children(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_get_children(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.accounts.with_raw_response.get_children(
                id="",
            )

    @parametrize
    def test_method_search(self, client: M3ter) -> None:
        account = client.accounts.search()
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    def test_method_search_with_all_params(self, client: M3ter) -> None:
        account = client.accounts.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    def test_raw_response_search(self, client: M3ter) -> None:
        response = client.accounts.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    def test_streaming_response_search(self, client: M3ter) -> None:
        with client.accounts.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountSearchResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAccounts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
            address={
                "address_line1": "addressLine1",
                "address_line2": "addressLine2",
                "address_line3": "addressLine3",
                "address_line4": "addressLine4",
                "country": "country",
                "locality": "locality",
                "post_code": "postCode",
                "region": "region",
            },
            auto_generate_statement_mode="NONE",
            bill_epoch=parse_date("2019-12-27"),
            config_data={"foo": "bar"},
            credit_application_order=["PREPAYMENT"],
            currency="USD",
            custom_fields={"foo": "string"},
            days_before_bill_due=1,
            parent_account_id="parentAccountId",
            purchase_order_number="purchaseOrderNumber",
            statement_definition_id="statementDefinitionId",
            version=0,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.create(
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.retrieve(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.accounts.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
            address={
                "address_line1": "addressLine1",
                "address_line2": "addressLine2",
                "address_line3": "addressLine3",
                "address_line4": "addressLine4",
                "country": "country",
                "locality": "locality",
                "post_code": "postCode",
                "region": "region",
            },
            auto_generate_statement_mode="NONE",
            bill_epoch=parse_date("2019-12-27"),
            config_data={"foo": "bar"},
            credit_application_order=["PREPAYMENT"],
            currency="USD",
            custom_fields={"foo": "string"},
            days_before_bill_due=1,
            parent_account_id="parentAccountId",
            purchase_order_number="purchaseOrderNumber",
            statement_definition_id="statementDefinitionId",
            version=0,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.update(
            id="id",
            code='S?oC"$]C] ]]]]]5]',
            email_address="dev@stainless.com",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.accounts.with_raw_response.update(
                id="",
                code='S?oC"$]C] ]]]]]5]',
                email_address="dev@stainless.com",
                name="x",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.list()
        assert_matches_type(AsyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.list(
            codes=["string"],
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AsyncCursor[AccountResponse], account, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AsyncCursor[AccountResponse], account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.delete(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.accounts.with_raw_response.delete(
                id="",
            )

    @parametrize
    async def test_method_end_date_billing_entities(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    async def test_method_end_date_billing_entities_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            apply_to_children=True,
        )
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_end_date_billing_entities(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_end_date_billing_entities(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.end_date_billing_entities(
            id="id",
            billing_entities=["CONTRACT"],
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountEndDateBillingEntitiesResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_end_date_billing_entities(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.accounts.with_raw_response.end_date_billing_entities(
                id="",
                billing_entities=["CONTRACT"],
                end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            )

    @parametrize
    async def test_method_get_children(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.get_children(
            id="id",
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_method_get_children_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.get_children(
            id="id",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_get_children(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.get_children(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_get_children(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.get_children(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_get_children(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.accounts.with_raw_response.get_children(
                id="",
            )

    @parametrize
    async def test_method_search(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.search()
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    async def test_method_search_with_all_params(self, async_client: AsyncM3ter) -> None:
        account = await async_client.accounts.search(
            from_document=0,
            operator="AND",
            page_size=1,
            search_query="searchQuery",
            sort_by="sortBy",
            sort_order="ASC",
        )
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    async def test_raw_response_search(self, async_client: AsyncM3ter) -> None:
        response = await async_client.accounts.with_raw_response.search()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountSearchResponse, account, path=["response"])

    @parametrize
    async def test_streaming_response_search(self, async_client: AsyncM3ter) -> None:
        async with async_client.accounts.with_streaming_response.search() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountSearchResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True
