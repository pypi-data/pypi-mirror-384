# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types import (
    AssistantObject,
    AssistantListResponse,
    AssistantDeleteResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAssistants:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.create(
            model="openai/gpt-oss-120b",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.create(
            model="openai/gpt-oss-120b",
            description="description",
            instructions="instructions",
            metadata={"foo": "string"},
            name="name",
            reasoning_effort="minimal",
            response_format="auto",
            temperature=1,
            tool_resources={
                "code_interpreter": {"file_ids": ["string"]},
                "file_search": {
                    "vector_store_ids": ["string"],
                    "vector_stores": [
                        {
                            "chunking_strategy": {"type": "auto"},
                            "file_ids": ["string"],
                            "metadata": {"foo": "string"},
                        }
                    ],
                },
            },
            tools=[{"type": "code_interpreter"}],
            top_p=1,
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.assistants.with_raw_response.create(
            model="openai/gpt-oss-120b",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.assistants.with_streaming_response.create(
            model="openai/gpt-oss-120b",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.retrieve(
            "assistant_id",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: ExcaiSDK) -> None:
        response = client.assistants.with_raw_response.retrieve(
            "assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: ExcaiSDK) -> None:
        with client.assistants.with_streaming_response.retrieve(
            "assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            client.assistants.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.update(
            assistant_id="assistant_id",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.update(
            assistant_id="assistant_id",
            description="description",
            instructions="instructions",
            metadata={"foo": "string"},
            model="string",
            name="name",
            reasoning_effort="minimal",
            response_format="auto",
            temperature=1,
            tool_resources={
                "code_interpreter": {"file_ids": ["string"]},
                "file_search": {"vector_store_ids": ["string"]},
            },
            tools=[{"type": "code_interpreter"}],
            top_p=1,
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: ExcaiSDK) -> None:
        response = client.assistants.with_raw_response.update(
            assistant_id="assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: ExcaiSDK) -> None:
        with client.assistants.with_streaming_response.update(
            assistant_id="assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            client.assistants.with_raw_response.update(
                assistant_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.list()
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.list(
            after="after",
            before="before",
            limit=0,
            order="asc",
        )
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: ExcaiSDK) -> None:
        response = client.assistants.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: ExcaiSDK) -> None:
        with client.assistants.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(AssistantListResponse, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: ExcaiSDK) -> None:
        assistant = client.assistants.delete(
            "assistant_id",
        )
        assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: ExcaiSDK) -> None:
        response = client.assistants.with_raw_response.delete(
            "assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = response.parse()
        assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: ExcaiSDK) -> None:
        with client.assistants.with_streaming_response.delete(
            "assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = response.parse()
            assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            client.assistants.with_raw_response.delete(
                "",
            )


class TestAsyncAssistants:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.create(
            model="openai/gpt-oss-120b",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.create(
            model="openai/gpt-oss-120b",
            description="description",
            instructions="instructions",
            metadata={"foo": "string"},
            name="name",
            reasoning_effort="minimal",
            response_format="auto",
            temperature=1,
            tool_resources={
                "code_interpreter": {"file_ids": ["string"]},
                "file_search": {
                    "vector_store_ids": ["string"],
                    "vector_stores": [
                        {
                            "chunking_strategy": {"type": "auto"},
                            "file_ids": ["string"],
                            "metadata": {"foo": "string"},
                        }
                    ],
                },
            },
            tools=[{"type": "code_interpreter"}],
            top_p=1,
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.assistants.with_raw_response.create(
            model="openai/gpt-oss-120b",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.assistants.with_streaming_response.create(
            model="openai/gpt-oss-120b",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.retrieve(
            "assistant_id",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.assistants.with_raw_response.retrieve(
            "assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.assistants.with_streaming_response.retrieve(
            "assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            await async_client.assistants.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.update(
            assistant_id="assistant_id",
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.update(
            assistant_id="assistant_id",
            description="description",
            instructions="instructions",
            metadata={"foo": "string"},
            model="string",
            name="name",
            reasoning_effort="minimal",
            response_format="auto",
            temperature=1,
            tool_resources={
                "code_interpreter": {"file_ids": ["string"]},
                "file_search": {"vector_store_ids": ["string"]},
            },
            tools=[{"type": "code_interpreter"}],
            top_p=1,
        )
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.assistants.with_raw_response.update(
            assistant_id="assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(AssistantObject, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.assistants.with_streaming_response.update(
            assistant_id="assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(AssistantObject, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            await async_client.assistants.with_raw_response.update(
                assistant_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.list()
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.list(
            after="after",
            before="before",
            limit=0,
            order="asc",
        )
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.assistants.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(AssistantListResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.assistants.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(AssistantListResponse, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncExcaiSDK) -> None:
        assistant = await async_client.assistants.delete(
            "assistant_id",
        )
        assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.assistants.with_raw_response.delete(
            "assistant_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        assistant = await response.parse()
        assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.assistants.with_streaming_response.delete(
            "assistant_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            assistant = await response.parse()
            assert_matches_type(AssistantDeleteResponse, assistant, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `assistant_id` but received ''"):
            await async_client.assistants.with_raw_response.delete(
                "",
            )
