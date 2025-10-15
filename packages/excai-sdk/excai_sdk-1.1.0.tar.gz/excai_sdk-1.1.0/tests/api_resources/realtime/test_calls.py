# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from excai_sdk import ExcaiSDK, AsyncExcaiSDK
from excai_sdk._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCalls:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_create(self, client: ExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        call = client.realtime.calls.create(
            sdp="sdp",
        )
        assert call.is_closed
        assert call.json() == {"foo": "bar"}
        assert cast(Any, call.is_closed) is True
        assert isinstance(call, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_create_with_all_params(self, client: ExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        call = client.realtime.calls.create(
            sdp="sdp",
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
        assert call.is_closed
        assert call.json() == {"foo": "bar"}
        assert cast(Any, call.is_closed) is True
        assert isinstance(call, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_create(self, client: ExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        call = client.realtime.calls.with_raw_response.create(
            sdp="sdp",
        )

        assert call.is_closed is True
        assert call.http_request.headers.get("X-Stainless-Lang") == "python"
        assert call.json() == {"foo": "bar"}
        assert isinstance(call, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_create(self, client: ExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.realtime.calls.with_streaming_response.create(
            sdp="sdp",
        ) as call:
            assert not call.is_closed
            assert call.http_request.headers.get("X-Stainless-Lang") == "python"

            assert call.json() == {"foo": "bar"}
            assert cast(Any, call.is_closed) is True
            assert isinstance(call, StreamedBinaryAPIResponse)

        assert cast(Any, call.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_accept(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.accept(
            call_id="call_id",
            type="realtime",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_accept_with_all_params(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.accept(
            call_id="call_id",
            type="realtime",
            audio={
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
            include=["item.input_audio_transcription.logprobs"],
            instructions="instructions",
            max_output_tokens=0,
            model="string",
            output_modalities=["text"],
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            tool_choice="none",
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
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_accept(self, client: ExcaiSDK) -> None:
        response = client.realtime.calls.with_raw_response.accept(
            call_id="call_id",
            type="realtime",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_accept(self, client: ExcaiSDK) -> None:
        with client.realtime.calls.with_streaming_response.accept(
            call_id="call_id",
            type="realtime",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_accept(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.realtime.calls.with_raw_response.accept(
                call_id="",
                type="realtime",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_hangup(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.hangup(
            "call_id",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_hangup(self, client: ExcaiSDK) -> None:
        response = client.realtime.calls.with_raw_response.hangup(
            "call_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_hangup(self, client: ExcaiSDK) -> None:
        with client.realtime.calls.with_streaming_response.hangup(
            "call_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_hangup(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.realtime.calls.with_raw_response.hangup(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_refer(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_refer(self, client: ExcaiSDK) -> None:
        response = client.realtime.calls.with_raw_response.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_refer(self, client: ExcaiSDK) -> None:
        with client.realtime.calls.with_streaming_response.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_refer(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.realtime.calls.with_raw_response.refer(
                call_id="",
                target_uri="tel:+14155550123",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reject(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.reject(
            call_id="call_id",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reject_with_all_params(self, client: ExcaiSDK) -> None:
        call = client.realtime.calls.reject(
            call_id="call_id",
            status_code=486,
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_reject(self, client: ExcaiSDK) -> None:
        response = client.realtime.calls.with_raw_response.reject(
            call_id="call_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_reject(self, client: ExcaiSDK) -> None:
        with client.realtime.calls.with_streaming_response.reject(
            call_id="call_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_reject(self, client: ExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            client.realtime.calls.with_raw_response.reject(
                call_id="",
            )


class TestAsyncCalls:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_create(self, async_client: AsyncExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        call = await async_client.realtime.calls.create(
            sdp="sdp",
        )
        assert call.is_closed
        assert await call.json() == {"foo": "bar"}
        assert cast(Any, call.is_closed) is True
        assert isinstance(call, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_create_with_all_params(self, async_client: AsyncExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        call = await async_client.realtime.calls.create(
            sdp="sdp",
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
        assert call.is_closed
        assert await call.json() == {"foo": "bar"}
        assert cast(Any, call.is_closed) is True
        assert isinstance(call, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_create(self, async_client: AsyncExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        call = await async_client.realtime.calls.with_raw_response.create(
            sdp="sdp",
        )

        assert call.is_closed is True
        assert call.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await call.json() == {"foo": "bar"}
        assert isinstance(call, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_create(self, async_client: AsyncExcaiSDK, respx_mock: MockRouter) -> None:
        respx_mock.post("/realtime/calls").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.realtime.calls.with_streaming_response.create(
            sdp="sdp",
        ) as call:
            assert not call.is_closed
            assert call.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await call.json() == {"foo": "bar"}
            assert cast(Any, call.is_closed) is True
            assert isinstance(call, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, call.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_accept(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.accept(
            call_id="call_id",
            type="realtime",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_accept_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.accept(
            call_id="call_id",
            type="realtime",
            audio={
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
            include=["item.input_audio_transcription.logprobs"],
            instructions="instructions",
            max_output_tokens=0,
            model="string",
            output_modalities=["text"],
            prompt={
                "id": "id",
                "variables": {"foo": "string"},
                "version": "version",
            },
            tool_choice="none",
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
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_accept(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.calls.with_raw_response.accept(
            call_id="call_id",
            type="realtime",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = await response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_accept(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.calls.with_streaming_response.accept(
            call_id="call_id",
            type="realtime",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = await response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_accept(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.realtime.calls.with_raw_response.accept(
                call_id="",
                type="realtime",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_hangup(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.hangup(
            "call_id",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_hangup(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.calls.with_raw_response.hangup(
            "call_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = await response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_hangup(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.calls.with_streaming_response.hangup(
            "call_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = await response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_hangup(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.realtime.calls.with_raw_response.hangup(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_refer(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_refer(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.calls.with_raw_response.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = await response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_refer(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.calls.with_streaming_response.refer(
            call_id="call_id",
            target_uri="tel:+14155550123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = await response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_refer(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.realtime.calls.with_raw_response.refer(
                call_id="",
                target_uri="tel:+14155550123",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reject(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.reject(
            call_id="call_id",
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reject_with_all_params(self, async_client: AsyncExcaiSDK) -> None:
        call = await async_client.realtime.calls.reject(
            call_id="call_id",
            status_code=486,
        )
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_reject(self, async_client: AsyncExcaiSDK) -> None:
        response = await async_client.realtime.calls.with_raw_response.reject(
            call_id="call_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        call = await response.parse()
        assert call is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_reject(self, async_client: AsyncExcaiSDK) -> None:
        async with async_client.realtime.calls.with_streaming_response.reject(
            call_id="call_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            call = await response.parse()
            assert call is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_reject(self, async_client: AsyncExcaiSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `call_id` but received ''"):
            await async_client.realtime.calls.with_raw_response.reject(
                call_id="",
            )
