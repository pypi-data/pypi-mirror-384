# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.fine_tuning.alpha import (
    GraderRunResponse,
    GraderValidateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGraders:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run(self, client: ExcaiSDK) -> None:
        grader = client.fine_tuning.alpha.graders.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        )
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_with_all_params(self, client: ExcaiSDK) -> None:
        grader = client.fine_tuning.alpha.graders.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
            item={},
        )
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run(self, client: ExcaiSDK) -> None:
        response = client.fine_tuning.alpha.graders.with_raw_response.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        grader = response.parse()
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run(self, client: ExcaiSDK) -> None:
        with client.fine_tuning.alpha.graders.with_streaming_response.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            grader = response.parse()
            assert_matches_type(GraderRunResponse, grader, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_validate(self, client: ExcaiSDK) -> None:
        grader = client.fine_tuning.alpha.graders.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_validate_with_all_params(self, client: ExcaiSDK) -> None:
        grader = client.fine_tuning.alpha.graders.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_validate(self, client: ExcaiSDK) -> None:
        response = client.fine_tuning.alpha.graders.with_raw_response.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        grader = response.parse()
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_validate(self, client: ExcaiSDK) -> None:
        with client.fine_tuning.alpha.graders.with_streaming_response.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            grader = response.parse()
            assert_matches_type(GraderValidateResponse, grader, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGraders:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run(self, async_client: AsyncExcaiSDK) -> None:
        grader = await async_client.fine_tuning.alpha.graders.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        )
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        grader = await async_client.fine_tuning.alpha.graders.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
            item={},
        )
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.fine_tuning.alpha.graders.with_raw_response.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        grader = await response.parse()
        assert_matches_type(GraderRunResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.fine_tuning.alpha.graders.with_streaming_response.run(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
            model_sample="model_sample",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            grader = await response.parse()
            assert_matches_type(GraderRunResponse, grader, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_validate(self, async_client: AsyncExcaiSDK) -> None:
        grader = await async_client.fine_tuning.alpha.graders.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_validate_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        grader = await async_client.fine_tuning.alpha.graders.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_validate(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.fine_tuning.alpha.graders.with_raw_response.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        grader = await response.parse()
        assert_matches_type(GraderValidateResponse, grader, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_validate(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.fine_tuning.alpha.graders.with_streaming_response.validate(
            grader={
                "input": "input",
                "name": "name",
                "operation": "eq",
                "reference": "reference",
                "type": "string_check",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            grader = await response.parse()
            assert_matches_type(GraderValidateResponse, grader, path=["response"])

        assert cast(Any, response.is_closed) is True
