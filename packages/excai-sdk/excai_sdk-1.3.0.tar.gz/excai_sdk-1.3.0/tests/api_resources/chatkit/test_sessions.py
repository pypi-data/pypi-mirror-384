# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types.chatkit import ChatSession

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSessions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: ExcaiSDK) -> None:
        session = client.chatkit.sessions.create(
            user="x",
            workflow={"id": "id"},
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: ExcaiSDK) -> None:
        session = client.chatkit.sessions.create(
            user="x",
            workflow={
                "id": "id",
                "state_variables": {"foo": "string"},
                "tracing": {"enabled": True},
                "version": "version",
            },
            chatkit_configuration={
                "automatic_thread_titling": {"enabled": True},
                "file_upload": {
                    "enabled": True,
                    "max_file_size": 1,
                    "max_files": 1,
                },
                "history": {
                    "enabled": True,
                    "recent_threads": 1,
                },
            },
            expires_after={
                "anchor": "created_at",
                "seconds": 1,
            },
            rate_limits={"max_requests_per_1_minute": 1},
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: ExcaiSDK) -> None:
        response = client.chatkit.sessions.with_raw_response.create(
            user="x",
            workflow={"id": "id"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: ExcaiSDK) -> None:
        with client.chatkit.sessions.with_streaming_response.create(
            user="x",
            workflow={"id": "id"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(ChatSession, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: ExcaiSDK) -> None:
        session = client.chatkit.sessions.cancel(
            "cksess_123",
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: ExcaiSDK) -> None:
        response = client.chatkit.sessions.with_raw_response.cancel(
            "cksess_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = response.parse()
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: ExcaiSDK) -> None:
        with client.chatkit.sessions.with_streaming_response.cancel(
            "cksess_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = response.parse()
            assert_matches_type(ChatSession, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            client.chatkit.sessions.with_raw_response.cancel(
                "",
            )


class TestAsyncSessions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncExcaiSDK) -> None:
        session = await async_client.chatkit.sessions.create(
            user="x",
            workflow={"id": "id"},
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        session = await async_client.chatkit.sessions.create(
            user="x",
            workflow={
                "id": "id",
                "state_variables": {"foo": "string"},
                "tracing": {"enabled": True},
                "version": "version",
            },
            chatkit_configuration={
                "automatic_thread_titling": {"enabled": True},
                "file_upload": {
                    "enabled": True,
                    "max_file_size": 1,
                    "max_files": 1,
                },
                "history": {
                    "enabled": True,
                    "recent_threads": 1,
                },
            },
            expires_after={
                "anchor": "created_at",
                "seconds": 1,
            },
            rate_limits={"max_requests_per_1_minute": 1},
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chatkit.sessions.with_raw_response.create(
            user="x",
            workflow={"id": "id"},
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chatkit.sessions.with_streaming_response.create(
            user="x",
            workflow={"id": "id"},
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(ChatSession, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncExcaiSDK) -> None:
        session = await async_client.chatkit.sessions.cancel(
            "cksess_123",
        )
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chatkit.sessions.with_raw_response.cancel(
            "cksess_123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        session = await response.parse()
        assert_matches_type(ChatSession, session, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chatkit.sessions.with_streaming_response.cancel(
            "cksess_123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            session = await response.parse()
            assert_matches_type(ChatSession, session, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `session_id` but received ''"):
            await async_client.chatkit.sessions.with_raw_response.cancel(
                "",
            )
