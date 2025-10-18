# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    ResourceGroupResponse,
    PermissionPolicyResponse,
    ResourceGroupListContentsResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestResourceGroups:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        resource_group = client.resource_groups.create(
            type="type",
            name="x",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.create(
            type="type",
            name="x",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.create(
            type="type",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.create(
            type="type",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_create(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.create(
                type="",
                name="x",
            )

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        resource_group = client.resource_groups.retrieve(
            id="id",
            type="type",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.retrieve(
            id="id",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.retrieve(
            id="id",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.retrieve(
                id="id",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.resource_groups.with_raw_response.retrieve(
                id="",
                type="type",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        resource_group = client.resource_groups.update(
            id="id",
            type="type",
            name="x",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.update(
            id="id",
            type="type",
            name="x",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.update(
            id="id",
            type="type",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.update(
            id="id",
            type="type",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.update(
                id="id",
                type="",
                name="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.resource_groups.with_raw_response.update(
                id="",
                type="type",
                name="x",
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list(
            type="type",
        )
        assert_matches_type(SyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list(
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.list(
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(SyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.list(
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(SyncCursor[ResourceGroupResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.list(
                type="",
            )

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        resource_group = client.resource_groups.delete(
            id="id",
            type="type",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.delete(
            id="id",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.delete(
            id="id",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.delete(
                id="id",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.resource_groups.with_raw_response.delete(
                id="",
                type="type",
            )

    @parametrize
    def test_method_add_resource(self, client: M3ter) -> None:
        resource_group = client.resource_groups.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_method_add_resource_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_add_resource(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_add_resource(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_add_resource(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.add_resource(
                resource_group_id="resourceGroupId",
                type="",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            client.resource_groups.with_raw_response.add_resource(
                resource_group_id="",
                type="type",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

    @parametrize
    def test_method_list_contents(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        )
        assert_matches_type(SyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    def test_method_list_contents_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    def test_raw_response_list_contents(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(SyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    def test_streaming_response_list_contents(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(SyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list_contents(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.list_contents(
                resource_group_id="resourceGroupId",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            client.resource_groups.with_raw_response.list_contents(
                resource_group_id="",
                type="type",
            )

    @parametrize
    def test_method_list_permissions(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        )
        assert_matches_type(SyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    def test_method_list_permissions_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    def test_raw_response_list_permissions(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(SyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    def test_streaming_response_list_permissions(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(SyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_list_permissions(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.list_permissions(
                resource_group_id="resourceGroupId",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            client.resource_groups.with_raw_response.list_permissions(
                resource_group_id="",
                type="type",
            )

    @parametrize
    def test_method_remove_resource(self, client: M3ter) -> None:
        resource_group = client.resource_groups.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_method_remove_resource_with_all_params(self, client: M3ter) -> None:
        resource_group = client.resource_groups.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_raw_response_remove_resource(self, client: M3ter) -> None:
        response = client.resource_groups.with_raw_response.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    def test_streaming_response_remove_resource(self, client: M3ter) -> None:
        with client.resource_groups.with_streaming_response.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_remove_resource(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            client.resource_groups.with_raw_response.remove_resource(
                resource_group_id="resourceGroupId",
                type="",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            client.resource_groups.with_raw_response.remove_resource(
                resource_group_id="",
                type="type",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )


class TestAsyncResourceGroups:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.create(
            type="type",
            name="x",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.create(
            type="type",
            name="x",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.create(
            type="type",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.create(
            type="type",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_create(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.create(
                type="",
                name="x",
            )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.retrieve(
            id="id",
            type="type",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.retrieve(
            id="id",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.retrieve(
            id="id",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.retrieve(
                id="id",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.resource_groups.with_raw_response.retrieve(
                id="",
                type="type",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.update(
            id="id",
            type="type",
            name="x",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.update(
            id="id",
            type="type",
            name="x",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.update(
            id="id",
            type="type",
            name="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.update(
            id="id",
            type="type",
            name="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.update(
                id="id",
                type="",
                name="x",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.resource_groups.with_raw_response.update(
                id="",
                type="type",
                name="x",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list(
            type="type",
        )
        assert_matches_type(AsyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list(
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.list(
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(AsyncCursor[ResourceGroupResponse], resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.list(
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(AsyncCursor[ResourceGroupResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.list(
                type="",
            )

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.delete(
            id="id",
            type="type",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.delete(
            id="id",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.delete(
            id="id",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.delete(
                id="id",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.resource_groups.with_raw_response.delete(
                id="",
                type="type",
            )

    @parametrize
    async def test_method_add_resource(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_method_add_resource_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_add_resource(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_add_resource(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.add_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_add_resource(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.add_resource(
                resource_group_id="resourceGroupId",
                type="",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            await async_client.resource_groups.with_raw_response.add_resource(
                resource_group_id="",
                type="type",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

    @parametrize
    async def test_method_list_contents(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        )
        assert_matches_type(AsyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    async def test_method_list_contents_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    async def test_raw_response_list_contents(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(AsyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_list_contents(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.list_contents(
            resource_group_id="resourceGroupId",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(AsyncCursor[ResourceGroupListContentsResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list_contents(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.list_contents(
                resource_group_id="resourceGroupId",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            await async_client.resource_groups.with_raw_response.list_contents(
                resource_group_id="",
                type="type",
            )

    @parametrize
    async def test_method_list_permissions(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        )
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    async def test_method_list_permissions_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    async def test_raw_response_list_permissions(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_list_permissions(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.list_permissions(
            resource_group_id="resourceGroupId",
            type="type",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(AsyncCursor[PermissionPolicyResponse], resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_list_permissions(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.list_permissions(
                resource_group_id="resourceGroupId",
                type="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            await async_client.resource_groups.with_raw_response.list_permissions(
                resource_group_id="",
                type="type",
            )

    @parametrize
    async def test_method_remove_resource(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_method_remove_resource_with_all_params(self, async_client: AsyncM3ter) -> None:
        resource_group = await async_client.resource_groups.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
            version=0,
        )
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_raw_response_remove_resource(self, async_client: AsyncM3ter) -> None:
        response = await async_client.resource_groups.with_raw_response.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        resource_group = await response.parse()
        assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

    @parametrize
    async def test_streaming_response_remove_resource(self, async_client: AsyncM3ter) -> None:
        async with async_client.resource_groups.with_streaming_response.remove_resource(
            resource_group_id="resourceGroupId",
            type="type",
            target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
            target_type="ITEM",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            resource_group = await response.parse()
            assert_matches_type(ResourceGroupResponse, resource_group, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_remove_resource(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `type` but received ''"):
            await async_client.resource_groups.with_raw_response.remove_resource(
                resource_group_id="resourceGroupId",
                type="",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `resource_group_id` but received ''"):
            await async_client.resource_groups.with_raw_response.remove_resource(
                resource_group_id="",
                type="type",
                target_id="06f6b50c-a868-4ca6-XXXX-448e507d5248",
                target_type="ITEM",
            )
