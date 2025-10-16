# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.fine_tuning.checkpoints import (
    PermissionDeleteResponse,
    ListFineTuningCheckpointPermissionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPermissions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        permission = client.fine_tuning.checkpoints.permissions.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.fine_tuning.checkpoints.permissions.with_raw_response.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = response.parse()
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.fine_tuning.checkpoints.permissions.with_streaming_response.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = response.parse()
            assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: ExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            client.fine_tuning.checkpoints.permissions.with_raw_response.create(
                fine_tuned_model_checkpoint="",
                project_ids=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        permission = client.fine_tuning.checkpoints.permissions.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        permission = client.fine_tuning.checkpoints.permissions.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
            after="after",
            limit=0,
            order="ascending",
            project_id="project_id",
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.fine_tuning.checkpoints.permissions.with_raw_response.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = response.parse()
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.fine_tuning.checkpoints.permissions.with_streaming_response.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = response.parse()
            assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: ExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            client.fine_tuning.checkpoints.permissions.with_raw_response.list(
                fine_tuned_model_checkpoint="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ExcaiSDK) -> None:
        permission = client.fine_tuning.checkpoints.permissions.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        )
        assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ExcaiSDK) -> None:
        response = client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = response.parse()
        assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ExcaiSDK) -> None:
        with client.fine_tuning.checkpoints.permissions.with_streaming_response.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = response.parse()
            assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
                permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
                fine_tuned_model_checkpoint="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_id` but received ''"):
            client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
                permission_id="",
                fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            )


class TestAsyncPermissions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        permission = await async_client.fine_tuning.checkpoints.permissions.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.fine_tuning.checkpoints.permissions.with_raw_response.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = await response.parse()
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.fine_tuning.checkpoints.permissions.with_streaming_response.create(
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            project_ids=["string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = await response.parse()
            assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            await async_client.fine_tuning.checkpoints.permissions.with_raw_response.create(
                fine_tuned_model_checkpoint="",
                project_ids=["string"],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        permission = await async_client.fine_tuning.checkpoints.permissions.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        permission = await async_client.fine_tuning.checkpoints.permissions.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
            after="after",
            limit=0,
            order="ascending",
            project_id="project_id",
        )
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.fine_tuning.checkpoints.permissions.with_raw_response.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = await response.parse()
        assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.fine_tuning.checkpoints.permissions.with_streaming_response.list(
            fine_tuned_model_checkpoint="ft-AF1WoRqd3aJAHsqc9NY7iL8F",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = await response.parse()
            assert_matches_type(ListFineTuningCheckpointPermissionResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            await async_client.fine_tuning.checkpoints.permissions.with_raw_response.list(
                fine_tuned_model_checkpoint="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncExcaiSDK) -> None:
        permission = await async_client.fine_tuning.checkpoints.permissions.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        )
        assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        permission = await response.parse()
        assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.fine_tuning.checkpoints.permissions.with_streaming_response.delete(
            permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
            fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            permission = await response.parse()
            assert_matches_type(PermissionDeleteResponse, permission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `fine_tuned_model_checkpoint` but received ''"
        ):
            await async_client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
                permission_id="cp_zc4Q7MP6XxulcVzj4MZdwsAB",
                fine_tuned_model_checkpoint="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `permission_id` but received ''"):
            await async_client.fine_tuning.checkpoints.permissions.with_raw_response.delete(
                permission_id="",
                fine_tuned_model_checkpoint="ft:gpt-4o-mini-2024-07-18:org:weather:B7R9VjQd",
            )
