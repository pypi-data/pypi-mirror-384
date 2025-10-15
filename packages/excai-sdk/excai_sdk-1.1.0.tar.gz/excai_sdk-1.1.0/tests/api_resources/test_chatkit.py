# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types import ChatkitUploadFileResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestChatkit:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_file(self, client: ExcaiSDK) -> None:
        chatkit = client.chatkit.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload_file(self, client: ExcaiSDK) -> None:
        response = client.chatkit.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chatkit = response.parse()
        assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload_file(self, client: ExcaiSDK) -> None:
        with client.chatkit.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chatkit = response.parse()
            assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncChatkit:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_file(self, async_client: AsyncExcaiSDK) -> None:
        chatkit = await async_client.chatkit.upload_file(
            file=b"raw file contents",
        )
        assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload_file(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.chatkit.with_raw_response.upload_file(
            file=b"raw file contents",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        chatkit = await response.parse()
        assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload_file(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.chatkit.with_streaming_response.upload_file(
            file=b"raw file contents",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            chatkit = await response.parse()
            assert_matches_type(ChatkitUploadFileResponse, chatkit, path=["response"])

        assert cast(Any, response.is_closed) is True
