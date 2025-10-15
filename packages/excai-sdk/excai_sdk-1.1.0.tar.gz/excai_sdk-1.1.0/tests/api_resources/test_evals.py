# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types import (
    Eval,
    EvalListResponse,
    EvalDeleteResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEvals:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        eval = client.evals.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ExcaiSDK) -> None:
        eval = client.evals.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
                "include_sample_schema": True,
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.evals.with_raw_response.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.evals.with_streaming_response.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ExcaiSDK) -> None:
        eval = client.evals.retrieve(
            "eval_id",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ExcaiSDK) -> None:
        response = client.evals.with_raw_response.retrieve(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ExcaiSDK) -> None:
        with client.evals.with_streaming_response.retrieve(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: ExcaiSDK) -> None:
        eval = client.evals.update(
            eval_id="eval_id",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: ExcaiSDK) -> None:
        eval = client.evals.update(
            eval_id="eval_id",
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: ExcaiSDK) -> None:
        response = client.evals.with_raw_response.update(
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: ExcaiSDK) -> None:
        with client.evals.with_streaming_response.update(
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.with_raw_response.update(
                eval_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        eval = client.evals.list()
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        eval = client.evals.list(
            after="after",
            limit=0,
            order="asc",
            order_by="created_at",
        )
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.evals.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = response.parse()
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.evals.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = response.parse()
            assert_matches_type(EvalListResponse, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ExcaiSDK) -> None:
        eval = client.evals.delete(
            "eval_id",
        )
        assert_matches_type(EvalDeleteResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ExcaiSDK) -> None:
        response = client.evals.with_raw_response.delete(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = response.parse()
        assert_matches_type(EvalDeleteResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ExcaiSDK) -> None:
        with client.evals.with_streaming_response.delete(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = response.parse()
            assert_matches_type(EvalDeleteResponse, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.with_raw_response.delete(
                "",
            )


class TestAsyncEvals:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
                "include_sample_schema": True,
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.with_raw_response.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = await response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.with_streaming_response.create(
            data_source_config={
                "item_schema": {"foo": "bar"},
                "type": "custom",
            },
            testing_criteria=[
                {
                    "input": [
                        {
                            "content": "content",
                            "role": "role",
                        }
                    ],
                    "labels": ["string"],
                    "model": "model",
                    "name": "name",
                    "passing_labels": ["string"],
                    "type": "label_model",
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = await response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.retrieve(
            "eval_id",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.with_raw_response.retrieve(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = await response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.with_streaming_response.retrieve(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = await response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.update(
            eval_id="eval_id",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.update(
            eval_id="eval_id",
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.with_raw_response.update(
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = await response.parse()
        assert_matches_type(Eval, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.with_streaming_response.update(
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = await response.parse()
            assert_matches_type(Eval, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.with_raw_response.update(
                eval_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.list()
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.list(
            after="after",
            limit=0,
            order="asc",
            order_by="created_at",
        )
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = await response.parse()
        assert_matches_type(EvalListResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = await response.parse()
            assert_matches_type(EvalListResponse, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncExcaiSDK) -> None:
        eval = await async_client.evals.delete(
            "eval_id",
        )
        assert_matches_type(EvalDeleteResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.with_raw_response.delete(
            "eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        eval = await response.parse()
        assert_matches_type(EvalDeleteResponse, eval, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.with_streaming_response.delete(
            "eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            eval = await response.parse()
            assert_matches_type(EvalDeleteResponse, eval, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.with_raw_response.delete(
                "",
            )
