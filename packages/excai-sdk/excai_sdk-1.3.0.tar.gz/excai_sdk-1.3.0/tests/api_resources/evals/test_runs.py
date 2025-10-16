# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.evals import EvalRun, RunListResponse, RunDeleteResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRuns:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [
                        {
                            "item": {"foo": "bar"},
                            "sample": {"foo": "bar"},
                        }
                    ],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.evals.runs.with_raw_response.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.evals.runs.with_streaming_response.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.runs.with_raw_response.create(
                eval_id="",
                data_source={
                    "source": {
                        "content": [{"item": {"foo": "bar"}}],
                        "type": "file_content",
                    },
                    "type": "jsonl",
                },
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ExcaiSDK) -> None:
        response = client.evals.runs.with_raw_response.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ExcaiSDK) -> None:
        with client.evals.runs.with_streaming_response.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.runs.with_raw_response.retrieve(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.evals.runs.with_raw_response.retrieve(
                run_id="",
                eval_id="eval_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.list(
            eval_id="eval_id",
        )
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.list(
            eval_id="eval_id",
            after="after",
            limit=0,
            order="asc",
            status="queued",
        )
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.evals.runs.with_raw_response.list(
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.evals.runs.with_streaming_response.list(
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunListResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.runs.with_raw_response.list(
                eval_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.delete(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(RunDeleteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ExcaiSDK) -> None:
        response = client.evals.runs.with_raw_response.delete(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(RunDeleteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ExcaiSDK) -> None:
        with client.evals.runs.with_streaming_response.delete(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(RunDeleteResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.runs.with_raw_response.delete(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.evals.runs.with_raw_response.delete(
                run_id="",
                eval_id="eval_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: ExcaiSDK) -> None:
        run = client.evals.runs.cancel(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: ExcaiSDK) -> None:
        response = client.evals.runs.with_raw_response.cancel(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: ExcaiSDK) -> None:
        with client.evals.runs.with_streaming_response.cancel(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            client.evals.runs.with_raw_response.cancel(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            client.evals.runs.with_raw_response.cancel(
                run_id="",
                eval_id="eval_id",
            )


class TestAsyncRuns:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [
                        {
                            "item": {"foo": "bar"},
                            "sample": {"foo": "bar"},
                        }
                    ],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
            metadata={"foo": "string"},
            name="name",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.runs.with_raw_response.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.runs.with_streaming_response.create(
            eval_id="eval_id",
            data_source={
                "source": {
                    "content": [{"item": {"foo": "bar"}}],
                    "type": "file_content",
                },
                "type": "jsonl",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.runs.with_raw_response.create(
                eval_id="",
                data_source={
                    "source": {
                        "content": [{"item": {"foo": "bar"}}],
                        "type": "file_content",
                    },
                    "type": "jsonl",
                },
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.runs.with_raw_response.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.runs.with_streaming_response.retrieve(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.runs.with_raw_response.retrieve(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.evals.runs.with_raw_response.retrieve(
                run_id="",
                eval_id="eval_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.list(
            eval_id="eval_id",
        )
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.list(
            eval_id="eval_id",
            after="after",
            limit=0,
            order="asc",
            status="queued",
        )
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.runs.with_raw_response.list(
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunListResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.runs.with_streaming_response.list(
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunListResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.runs.with_raw_response.list(
                eval_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.delete(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(RunDeleteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.runs.with_raw_response.delete(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(RunDeleteResponse, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.runs.with_streaming_response.delete(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(RunDeleteResponse, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.runs.with_raw_response.delete(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.evals.runs.with_raw_response.delete(
                run_id="",
                eval_id="eval_id",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncExcaiSDK) -> None:
        run = await async_client.evals.runs.cancel(
            run_id="run_id",
            eval_id="eval_id",
        )
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.evals.runs.with_raw_response.cancel(
            run_id="run_id",
            eval_id="eval_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        run = await response.parse()
        assert_matches_type(EvalRun, run, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.evals.runs.with_streaming_response.cancel(
            run_id="run_id",
            eval_id="eval_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            run = await response.parse()
            assert_matches_type(EvalRun, run, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `eval_id` but received ''"):
            await async_client.evals.runs.with_raw_response.cancel(
                run_id="run_id",
                eval_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `run_id` but received ''"):
            await async_client.evals.runs.with_raw_response.cancel(
                run_id="",
                eval_id="eval_id",
            )
