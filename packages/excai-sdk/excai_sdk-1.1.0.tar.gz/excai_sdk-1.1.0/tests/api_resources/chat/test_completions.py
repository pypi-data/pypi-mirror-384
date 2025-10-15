# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.chat import (
    CreateResponse,
    CompletionListResponse,
    CompletionDeleteResponse,
    CompletionGetMessagesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCompletions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.create(
            body={
                "top_logprobs": 0,
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                        "name": "name",
                    }
                ],
                "model": "gpt-4o",
                "audio": {
                    "format": "wav",
                    "voice": "ash",
                },
                "frequency_penalty": -2,
                "function_call": "none",
                "functions": [
                    {
                        "name": "name",
                        "description": "description",
                        "parameters": {"foo": "bar"},
                    }
                ],
                "logit_bias": {"foo": 0},
                "logprobs": True,
                "max_completion_tokens": 0,
                "max_tokens": 0,
                "modalities": ["text"],
                "n": 1,
                "parallel_tool_calls": True,
                "prediction": {
                    "content": "string",
                    "type": "content",
                },
                "presence_penalty": -2,
                "reasoning_effort": "minimal",
                "response_format": {"type": "text"},
                "seed": -9007199254740991,
                "stop": "\n",
                "store": True,
                "stream": True,
                "stream_options": {
                    "include_obfuscation": True,
                    "include_usage": True,
                },
                "tool_choice": "none",
                "tools": [
                    {
                        "function": {
                            "name": "name",
                            "description": "description",
                            "parameters": {"foo": "bar"},
                            "strict": True,
                        },
                        "type": "function",
                    }
                ],
                "verbosity": "low",
                "web_search_options": {
                    "search_context_size": "low",
                    "user_location": {
                        "approximate": {
                            "city": "city",
                            "country": "country",
                            "region": "region",
                            "timezone": "timezone",
                        },
                        "type": "approximate",
                    },
                },
            },
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.retrieve(
            "completion_id",
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.retrieve(
            "completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.retrieve(
            "completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            client.chat.completions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            client.chat.completions.with_raw_response.update(
                completion_id="",
                metadata={"foo": "string"},
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.list()
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.list(
            after="after",
            limit=0,
            metadata={"foo": "string"},
            model="model",
            order="asc",
        )
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CompletionListResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.delete(
            "completion_id",
        )
        assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.delete(
            "completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.delete(
            "completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            client.chat.completions.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_messages(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.get_messages(
            completion_id="completion_id",
        )
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_messages_with_all_params(self, client: ExcaiSDK) -> None:
        completion = client.chat.completions.get_messages(
            completion_id="completion_id",
            after="after",
            limit=0,
            order="asc",
        )
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_messages(self, client: ExcaiSDK) -> None:
        response = client.chat.completions.with_raw_response.get_messages(
            completion_id="completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = response.parse()
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_messages(self, client: ExcaiSDK) -> None:
        with client.chat.completions.with_streaming_response.get_messages(
            completion_id="completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = response.parse()
            assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_messages(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            client.chat.completions.with_raw_response.get_messages(
                completion_id="",
            )


class TestAsyncCompletions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.create(
            body={
                "top_logprobs": 0,
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                        "name": "name",
                    }
                ],
                "model": "gpt-4o",
                "audio": {
                    "format": "wav",
                    "voice": "ash",
                },
                "frequency_penalty": -2,
                "function_call": "none",
                "functions": [
                    {
                        "name": "name",
                        "description": "description",
                        "parameters": {"foo": "bar"},
                    }
                ],
                "logit_bias": {"foo": 0},
                "logprobs": True,
                "max_completion_tokens": 0,
                "max_tokens": 0,
                "modalities": ["text"],
                "n": 1,
                "parallel_tool_calls": True,
                "prediction": {
                    "content": "string",
                    "type": "content",
                },
                "presence_penalty": -2,
                "reasoning_effort": "minimal",
                "response_format": {"type": "text"},
                "seed": -9007199254740991,
                "stop": "\n",
                "store": True,
                "stream": True,
                "stream_options": {
                    "include_obfuscation": True,
                    "include_usage": True,
                },
                "tool_choice": "none",
                "tools": [
                    {
                        "function": {
                            "name": "name",
                            "description": "description",
                            "parameters": {"foo": "bar"},
                            "strict": True,
                        },
                        "type": "function",
                    }
                ],
                "verbosity": "low",
                "web_search_options": {
                    "search_context_size": "low",
                    "user_location": {
                        "approximate": {
                            "city": "city",
                            "country": "country",
                            "region": "region",
                            "timezone": "timezone",
                        },
                        "type": "approximate",
                    },
                },
            },
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.create(
            body={
                "messages": [
                    {
                        "content": "string",
                        "role": "developer",
                    }
                ],
                "model": "gpt-4o",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.retrieve(
            "completion_id",
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.retrieve(
            "completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.retrieve(
            "completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            await async_client.chat.completions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        )
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CreateResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.update(
            completion_id="completion_id",
            metadata={"foo": "string"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CreateResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            await async_client.chat.completions.with_raw_response.update(
                completion_id="",
                metadata={"foo": "string"},
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.list()
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.list(
            after="after",
            limit=0,
            metadata={"foo": "string"},
            model="model",
            order="asc",
        )
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CompletionListResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CompletionListResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.delete(
            "completion_id",
        )
        assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.delete(
            "completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.delete(
            "completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CompletionDeleteResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            await async_client.chat.completions.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_messages(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.get_messages(
            completion_id="completion_id",
        )
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_messages_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        completion = await async_client.chat.completions.get_messages(
            completion_id="completion_id",
            after="after",
            limit=0,
            order="asc",
        )
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_messages(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chat.completions.with_raw_response.get_messages(
            completion_id="completion_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        completion = await response.parse()
        assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_messages(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chat.completions.with_streaming_response.get_messages(
            completion_id="completion_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            completion = await response.parse()
            assert_matches_type(CompletionGetMessagesResponse, completion, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_messages(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `completion_id` but received ''"):
            await async_client.chat.completions.with_raw_response.get_messages(
                completion_id="",
            )
