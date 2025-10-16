# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from tests.utils import assert_matches_type
from excai_sdk.types import (
    RealtimeCreateSessionResponse,
    RealtimeCreateClientSecretResponse,
    RealtimeCreateTranscriptionSessionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRealtime:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_client_secret(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_client_secret()
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_client_secret_with_all_params(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_client_secret(
            expires_after={
                "anchor": "created_at",
                "seconds": 10,
            },
            session={
                "type": "realtime",
                "audio": {
                    "input": {
                        "format": {
                            "rate": 24000,
                            "type": "audio/pcm",
                        },
                        "noise_reduction": {"type": "near_field"},
                        "transcription": {
                            "language": "language",
                            "model": "whisper-1",
                            "prompt": "prompt",
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "create_response": True,
                            "idle_timeout_ms": 5000,
                            "interrupt_response": True,
                            "prefix_padding_ms": 0,
                            "silence_duration_ms": 0,
                            "threshold": 0,
                        },
                    },
                    "output": {
                        "format": {
                            "rate": 24000,
                            "type": "audio/pcm",
                        },
                        "speed": 0.25,
                        "voice": "ash",
                    },
                },
                "include": ["item.input_audio_transcription.logprobs"],
                "instructions": "instructions",
                "max_output_tokens": 0,
                "model": "string",
                "output_modalities": ["text"],
                "prompt": {
                    "id": "id",
                    "variables": {"foo": "string"},
                    "version": "version",
                },
                "tool_choice": "none",
                "tools": [
                    {
                        "description": "description",
                        "name": "name",
                        "parameters": {},
                        "type": "function",
                    }
                ],
                "tracing": "auto",
                "truncation": "auto",
            },
        )
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_client_secret(self, client: ExcaiSDK) -> None:
        response = client.realtime.with_raw_response.create_client_secret()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = response.parse()
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_client_secret(self, client: ExcaiSDK) -> None:
        with client.realtime.with_streaming_response.create_client_secret() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = response.parse()
            assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_session(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        )
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_session_with_all_params(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
            input_audio_format="input_audio_format",
            input_audio_transcription={"model": "model"},
            instructions="instructions",
            max_response_output_tokens=0,
            modalities=["text"],
            output_audio_format="output_audio_format",
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            speed=0.25,
            temperature=0,
            tool_choice="tool_choice",
            tools=[
                {
                    "description": "description",
                    "name": "name",
                    "parameters": {},
                    "type": "function",
                }
            ],
            tracing="auto",
            truncation="auto",
            turn_detection={
                "prefix_padding_ms": 0,
                "silence_duration_ms": 0,
                "threshold": 0,
                "type": "type",
            },
            voice="ash",
        )
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_session(self, client: ExcaiSDK) -> None:
        response = client.realtime.with_raw_response.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = response.parse()
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_session(self, client: ExcaiSDK) -> None:
        with client.realtime.with_streaming_response.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = response.parse()
            assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_transcription_session(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_transcription_session()
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_transcription_session_with_all_params(self, client: ExcaiSDK) -> None:
        realtime = client.realtime.create_transcription_session(
            include=["item.input_audio_transcription.logprobs"],
            input_audio_format="pcm16",
            input_audio_noise_reduction={"type": "near_field"},
            input_audio_transcription={
                "language": "language",
                "model": "whisper-1",
                "prompt": "prompt",
            },
            turn_detection={
                "prefix_padding_ms": 0,
                "silence_duration_ms": 0,
                "threshold": 0,
                "type": "server_vad",
            },
        )
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_transcription_session(self, client: ExcaiSDK) -> None:
        response = client.realtime.with_raw_response.create_transcription_session()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = response.parse()
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_transcription_session(self, client: ExcaiSDK) -> None:
        with client.realtime.with_streaming_response.create_transcription_session() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = response.parse()
            assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncRealtime:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_client_secret(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_client_secret()
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_client_secret_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_client_secret(
            expires_after={
                "anchor": "created_at",
                "seconds": 10,
            },
            session={
                "type": "realtime",
                "audio": {
                    "input": {
                        "format": {
                            "rate": 24000,
                            "type": "audio/pcm",
                        },
                        "noise_reduction": {"type": "near_field"},
                        "transcription": {
                            "language": "language",
                            "model": "whisper-1",
                            "prompt": "prompt",
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "create_response": True,
                            "idle_timeout_ms": 5000,
                            "interrupt_response": True,
                            "prefix_padding_ms": 0,
                            "silence_duration_ms": 0,
                            "threshold": 0,
                        },
                    },
                    "output": {
                        "format": {
                            "rate": 24000,
                            "type": "audio/pcm",
                        },
                        "speed": 0.25,
                        "voice": "ash",
                    },
                },
                "include": ["item.input_audio_transcription.logprobs"],
                "instructions": "instructions",
                "max_output_tokens": 0,
                "model": "string",
                "output_modalities": ["text"],
                "prompt": {
                    "id": "id",
                    "variables": {"foo": "string"},
                    "version": "version",
                },
                "tool_choice": "none",
                "tools": [
                    {
                        "description": "description",
                        "name": "name",
                        "parameters": {},
                        "type": "function",
                    }
                ],
                "tracing": "auto",
                "truncation": "auto",
            },
        )
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_client_secret(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.with_raw_response.create_client_secret()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = await response.parse()
        assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_client_secret(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.with_streaming_response.create_client_secret() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = await response.parse()
            assert_matches_type(RealtimeCreateClientSecretResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_session(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        )
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_session_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
            input_audio_format="input_audio_format",
            input_audio_transcription={"model": "model"},
            instructions="instructions",
            max_response_output_tokens=0,
            modalities=["text"],
            output_audio_format="output_audio_format",
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            speed=0.25,
            temperature=0,
            tool_choice="tool_choice",
            tools=[
                {
                    "description": "description",
                    "name": "name",
                    "parameters": {},
                    "type": "function",
                }
            ],
            tracing="auto",
            truncation="auto",
            turn_detection={
                "prefix_padding_ms": 0,
                "silence_duration_ms": 0,
                "threshold": 0,
                "type": "type",
            },
            voice="ash",
        )
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_session(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.with_raw_response.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = await response.parse()
        assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_session(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.with_streaming_response.create_session(
            client_secret={
                "expires_at": 0,
                "value": "value",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = await response.parse()
            assert_matches_type(RealtimeCreateSessionResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_transcription_session(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_transcription_session()
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_transcription_session_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        realtime = await async_client.realtime.create_transcription_session(
            include=["item.input_audio_transcription.logprobs"],
            input_audio_format="pcm16",
            input_audio_noise_reduction={"type": "near_field"},
            input_audio_transcription={
                "language": "language",
                "model": "whisper-1",
                "prompt": "prompt",
            },
            turn_detection={
                "prefix_padding_ms": 0,
                "silence_duration_ms": 0,
                "threshold": 0,
                "type": "server_vad",
            },
        )
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_transcription_session(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.with_raw_response.create_transcription_session()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        realtime = await response.parse()
        assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_transcription_session(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.with_streaming_response.create_transcription_session() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            realtime = await response.parse()
            assert_matches_type(RealtimeCreateTranscriptionSessionResponse, realtime, path=["response"])

        assert cast(Any, response.is_closed) is True
