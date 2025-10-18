# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor
from m3ter.types.data_exports import (
    DestinationCreateResponse,
    DestinationDeleteResponse,
    DestinationUpdateResponse,
    DestinationRetrieveResponse,
    DataExportDestinationResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDestinations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create_overload_1(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_1(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
            destination_type="S3",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            version=0,
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_create_overload_1(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_1(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationCreateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_create_overload_2(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_method_create_with_all_params_overload_2(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
            destination_type="GCS",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            service_account_email="serviceAccountEmail",
            version=0,
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_create_overload_2(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_create_overload_2(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationCreateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.retrieve(
            id="id",
        )
        assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.data_exports.destinations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update_overload_1(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_method_update_with_all_params_overload_1(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
            destination_type="S3",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            version=0,
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_update_overload_1(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_update_overload_1(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_overload_1(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.data_exports.destinations.with_raw_response.update(
                id="",
                bucket_name="xxx",
                iam_role_arn='arn:aws:iam::321669910225:role/"',
            )

    @parametrize
    def test_method_update_overload_2(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_method_update_with_all_params_overload_2(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
            destination_type="GCS",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            service_account_email="serviceAccountEmail",
            version=0,
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_update_overload_2(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_update_overload_2(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update_overload_2(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.data_exports.destinations.with_raw_response.update(
                id="",
                bucket_name="xxx",
                pool_id="x",
                project_number="x",
                provider_id="x",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.list()
        assert_matches_type(SyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.list(
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(SyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(SyncCursor[DataExportDestinationResponse], destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        destination = client.data_exports.destinations.delete(
            id="id",
        )
        assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.data_exports.destinations.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = response.parse()
        assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.data_exports.destinations.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = response.parse()
            assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.data_exports.destinations.with_raw_response.delete(
                id="",
            )


class TestAsyncDestinations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create_overload_1(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_1(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
            destination_type="S3",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            version=0,
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_1(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_1(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.create(
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationCreateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_create_overload_2(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_method_create_with_all_params_overload_2(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
            destination_type="GCS",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            service_account_email="serviceAccountEmail",
            version=0,
        )
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_create_overload_2(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationCreateResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_create_overload_2(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.create(
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationCreateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.retrieve(
            id="id",
        )
        assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationRetrieveResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.data_exports.destinations.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update_overload_1(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_method_update_with_all_params_overload_1(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
            destination_type="S3",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            version=0,
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_update_overload_1(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_update_overload_1(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.update(
            id="id",
            bucket_name="xxx",
            iam_role_arn='arn:aws:iam::321669910225:role/"',
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_overload_1(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.data_exports.destinations.with_raw_response.update(
                id="",
                bucket_name="xxx",
                iam_role_arn='arn:aws:iam::321669910225:role/"',
            )

    @parametrize
    async def test_method_update_overload_2(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_method_update_with_all_params_overload_2(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
            destination_type="GCS",
            partition_order="TYPE_FIRST",
            prefix="prefix",
            service_account_email="serviceAccountEmail",
            version=0,
        )
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_update_overload_2(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_update_overload_2(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.update(
            id="id",
            bucket_name="xxx",
            pool_id="x",
            project_number="x",
            provider_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationUpdateResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update_overload_2(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.data_exports.destinations.with_raw_response.update(
                id="",
                bucket_name="xxx",
                pool_id="x",
                project_number="x",
                provider_id="x",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.list()
        assert_matches_type(AsyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.list(
            ids=["string"],
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(AsyncCursor[DataExportDestinationResponse], destination, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(AsyncCursor[DataExportDestinationResponse], destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        destination = await async_client.data_exports.destinations.delete(
            id="id",
        )
        assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.data_exports.destinations.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        destination = await response.parse()
        assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.data_exports.destinations.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            destination = await response.parse()
            assert_matches_type(DestinationDeleteResponse, destination, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.data_exports.destinations.with_raw_response.delete(
                id="",
            )
