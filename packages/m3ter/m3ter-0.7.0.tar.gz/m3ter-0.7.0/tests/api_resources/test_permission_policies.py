# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from m3ter import M3ter, AsyncM3ter
from m3ter.types import (
    PermissionPolicyResponse,
    PermissionPolicyAddToUserResponse,
    PermissionPolicyAddToUserGroupResponse,
    PermissionPolicyRemoveFromUserResponse,
    PermissionPolicyAddToServiceUserResponse,
    PermissionPolicyAddToSupportUserResponse,
    PermissionPolicyRemoveFromUserGroupResponse,
    PermissionPolicyRemoveFromServiceUserResponse,
    PermissionPolicyRemoveFromSupportUserResponse,
)
from tests.utils import assert_matches_type
from m3ter.pagination import SyncCursor, AsyncCursor

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPermissionPolicies:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
            version=0,
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.retrieve(
            id="id",
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.permission_policies.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    def test_method_update(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
            version=0,
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.permission_policies.with_raw_response.update(
                id="",
                name="x",
                permission_policy=[
                    {
                        "action": ["ALL"],
                        "effect": "ALLOW",
                        "resource": ["string"],
                    }
                ],
            )

    @parametrize
    def test_method_list(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.list()
        assert_matches_type(SyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(SyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(SyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(SyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.delete(
            id="id",
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.permission_policies.with_raw_response.delete(
                id="",
            )

    @parametrize
    def test_method_add_to_service_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_add_to_service_user_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_add_to_service_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_add_to_service_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_add_to_service_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.add_to_service_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    def test_method_add_to_support_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        )
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_add_to_support_user_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_support_user(
            permission_policy_id="permissionPolicyId",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_add_to_support_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_add_to_support_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_add_to_support_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.add_to_support_user(
                permission_policy_id="",
            )

    @parametrize
    def test_method_add_to_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_add_to_user_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_add_to_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_add_to_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_add_to_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.add_to_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    def test_method_add_to_user_group(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_add_to_user_group_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_add_to_user_group(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_add_to_user_group(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_add_to_user_group(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.add_to_user_group(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    def test_method_remove_from_service_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_remove_from_service_user_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_remove_from_service_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_remove_from_service_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_remove_from_service_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.remove_from_service_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    def test_method_remove_from_support_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        )
        assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_remove_from_support_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_remove_from_support_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_remove_from_support_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.remove_from_support_user(
                permission_policy_id="",
            )

    @parametrize
    def test_method_remove_from_user(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_remove_from_user_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_remove_from_user(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_remove_from_user(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_remove_from_user(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.remove_from_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    def test_method_remove_from_user_group(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_method_remove_from_user_group_with_all_params(self, client: M3ter) -> None:
        permission_policy = client.permission_policies.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_raw_response_remove_from_user_group(self, client: M3ter) -> None:
        response = client.permission_policies.with_raw_response.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = response.parse()
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    def test_streaming_response_remove_from_user_group(self, client: M3ter) -> None:
        with client.permission_policies.with_streaming_response.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = response.parse()
            assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_remove_from_user_group(self, client: M3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            client.permission_policies.with_raw_response.remove_from_user_group(
                permission_policy_id="",
                principal_id="x",
            )


class TestAsyncPermissionPolicies:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
            version=0,
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.create(
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.retrieve(
            id="id",
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.retrieve(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.retrieve(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.permission_policies.with_raw_response.retrieve(
                id="",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
            version=0,
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.update(
            id="id",
            name="x",
            permission_policy=[
                {
                    "action": ["ALL"],
                    "effect": "ALLOW",
                    "resource": ["string"],
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.permission_policies.with_raw_response.update(
                id="",
                name="x",
                permission_policy=[
                    {
                        "action": ["ALL"],
                        "effect": "ALLOW",
                        "resource": ["string"],
                    }
                ],
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.list()
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.list(
            next_token="nextToken",
            page_size=1,
        )
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(AsyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(AsyncCursor[PermissionPolicyResponse], permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.delete(
            id="id",
        )
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.permission_policies.with_raw_response.delete(
                id="",
            )

    @parametrize
    async def test_method_add_to_service_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_add_to_service_user_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_add_to_service_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_add_to_service_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.add_to_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyAddToServiceUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_add_to_service_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.add_to_service_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    async def test_method_add_to_support_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        )
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_add_to_support_user_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_support_user(
            permission_policy_id="permissionPolicyId",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_add_to_support_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_add_to_support_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.add_to_support_user(
            permission_policy_id="permissionPolicyId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyAddToSupportUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_add_to_support_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.add_to_support_user(
                permission_policy_id="",
            )

    @parametrize
    async def test_method_add_to_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_add_to_user_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_add_to_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_add_to_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.add_to_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyAddToUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_add_to_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.add_to_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    async def test_method_add_to_user_group(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_add_to_user_group_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_add_to_user_group(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_add_to_user_group(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.add_to_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyAddToUserGroupResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_add_to_user_group(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.add_to_user_group(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    async def test_method_remove_from_service_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_remove_from_service_user_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_remove_from_service_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_remove_from_service_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.remove_from_service_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyRemoveFromServiceUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_remove_from_service_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.remove_from_service_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    async def test_method_remove_from_support_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        )
        assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_remove_from_support_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_remove_from_support_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.remove_from_support_user(
            permission_policy_id="permissionPolicyId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyRemoveFromSupportUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_remove_from_support_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.remove_from_support_user(
                permission_policy_id="",
            )

    @parametrize
    async def test_method_remove_from_user(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_remove_from_user_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_remove_from_user(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_remove_from_user(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.remove_from_user(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyRemoveFromUserResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_remove_from_user(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.remove_from_user(
                permission_policy_id="",
                principal_id="x",
            )

    @parametrize
    async def test_method_remove_from_user_group(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_method_remove_from_user_group_with_all_params(self, async_client: AsyncM3ter) -> None:
        permission_policy = await async_client.permission_policies.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
            version=0,
        )
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_raw_response_remove_from_user_group(self, async_client: AsyncM3ter) -> None:
        response = await async_client.permission_policies.with_raw_response.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission_policy = await response.parse()
        assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

    @parametrize
    async def test_streaming_response_remove_from_user_group(self, async_client: AsyncM3ter) -> None:
        async with async_client.permission_policies.with_streaming_response.remove_from_user_group(
            permission_policy_id="permissionPolicyId",
            principal_id="x",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission_policy = await response.parse()
            assert_matches_type(PermissionPolicyRemoveFromUserGroupResponse, permission_policy, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_remove_from_user_group(self, async_client: AsyncM3ter) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_policy_id` but received ''"):
            await async_client.permission_policies.with_raw_response.remove_from_user_group(
                permission_policy_id="",
                principal_id="x",
            )
