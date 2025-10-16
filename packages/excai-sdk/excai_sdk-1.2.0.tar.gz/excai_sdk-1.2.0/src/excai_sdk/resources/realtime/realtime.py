# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal

import httpx

from .calls import (
    CallsResource,
    AsyncCallsResource,
    CallsResourceWithRawResponse,
    AsyncCallsResourceWithRawResponse,
    CallsResourceWithStreamingResponse,
    AsyncCallsResourceWithStreamingResponse,
)
from ...types import (
    realtime_create_session_params,
    realtime_create_client_secret_params,
    realtime_create_transcription_session_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.realtime.prompt_param import PromptParam
from ...types.voice_ids_shared_param import VoiceIDsSharedParam
from ...types.audio_transcription_param import AudioTranscriptionParam
from ...types.realtime_create_session_response import RealtimeCreateSessionResponse
from ...types.realtime.realtime_truncation_param import RealtimeTruncationParam
from ...types.realtime_create_client_secret_response import RealtimeCreateClientSecretResponse
from ...types.realtime_create_transcription_session_response import RealtimeCreateTranscriptionSessionResponse

__all__ = ["RealtimeResource", "AsyncRealtimeResource"]


class RealtimeResource(SyncAPIResource):
    @cached_property
    def calls(self) -> CallsResource:
        return CallsResource(self._client)

    @cached_property
    def with_raw_response(self) -> RealtimeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return RealtimeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RealtimeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return RealtimeResourceWithStreamingResponse(self)

    def create_client_secret(
        self,
        *,
        expires_after: realtime_create_client_secret_params.ExpiresAfter | Omit = omit,
        session: realtime_create_client_secret_params.Session | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateClientSecretResponse:
        """
        Create a Realtime client secret with an associated session configuration.

        Args:
          expires_after: Configuration for the client secret expiration. Expiration refers to the time
              after which a client secret will no longer be valid for creating sessions. The
              session itself may continue after that time once started. A secret can be used
              to create multiple sessions until it expires.

          session: Session configuration to use for the client secret. Choose either a realtime
              session or a transcription session.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/realtime/client_secrets",
            body=maybe_transform(
                {
                    "expires_after": expires_after,
                    "session": session,
                },
                realtime_create_client_secret_params.RealtimeCreateClientSecretParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateClientSecretResponse,
        )

    def create_session(
        self,
        *,
        client_secret: realtime_create_session_params.ClientSecret,
        input_audio_format: str | Omit = omit,
        input_audio_transcription: realtime_create_session_params.InputAudioTranscription | Omit = omit,
        instructions: str | Omit = omit,
        max_response_output_tokens: Union[int, Literal["inf"]] | Omit = omit,
        modalities: List[Literal["text", "audio"]] | Omit = omit,
        output_audio_format: str | Omit = omit,
        prompt: Optional[PromptParam] | Omit = omit,
        speed: float | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: str | Omit = omit,
        tools: Iterable[realtime_create_session_params.Tool] | Omit = omit,
        tracing: realtime_create_session_params.Tracing | Omit = omit,
        truncation: RealtimeTruncationParam | Omit = omit,
        turn_detection: realtime_create_session_params.TurnDetection | Omit = omit,
        voice: VoiceIDsSharedParam | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateSessionResponse:
        """
        Create an ephemeral API token for use in client-side applications with the
        Realtime API. Can be configured with the same session parameters as the
        `session.update` client event.

        It responds with a session object, plus a `client_secret` key which contains a
        usable ephemeral API token that can be used to authenticate browser clients for
        the Realtime API.

        Args:
          client_secret: Ephemeral key returned by the API.

          input_audio_format: The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`.

          input_audio_transcription: Configuration for input audio transcription, defaults to off and can be set to
              `null` to turn off once on. Input audio transcription is not native to the
              model, since the model consumes audio directly. Transcription runs
              asynchronously and should be treated as rough guidance rather than the
              representation understood by the model.

          instructions: The default system instructions (i.e. system message) prepended to model calls.
              This field allows the client to guide the model on desired responses. The model
              can be instructed on response content and format, (e.g. "be extremely succinct",
              "act friendly", "here are examples of good responses") and on audio behavior
              (e.g. "talk quickly", "inject emotion into your voice", "laugh frequently"). The
              instructions are not guaranteed to be followed by the model, but they provide
              guidance to the model on the desired behavior. Note that the server sets default
              instructions which will be used if this field is not set and are visible in the
              `session.created` event at the start of the session.

          max_response_output_tokens: Maximum number of output tokens for a single assistant response, inclusive of
              tool calls. Provide an integer between 1 and 4096 to limit output tokens, or
              `inf` for the maximum available tokens for a given model. Defaults to `inf`.

          modalities: The set of modalities the model can respond with. To disable audio, set this to
              ["text"].

          output_audio_format: The format of output audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`.

          prompt: Reference to a prompt template and its variables.
              [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).

          speed: The speed of the model's spoken response. 1.0 is the default speed. 0.25 is the
              minimum speed. 1.5 is the maximum speed. This value can only be changed in
              between model turns, not while a response is in progress.

          temperature: Sampling temperature for the model, limited to [0.6, 1.2]. Defaults to 0.8.

          tool_choice: How the model chooses tools. Options are `auto`, `none`, `required`, or specify
              a function.

          tools: Tools (functions) available to the model.

          tracing: Configuration options for tracing. Set to null to disable tracing. Once tracing
              is enabled for a session, the configuration cannot be modified.

              `auto` will create a trace for the session with default values for the workflow
              name, group id, and metadata.

          truncation: Controls how the realtime conversation is truncated prior to model inference.
              The default is `auto`.

          turn_detection: Configuration for turn detection. Can be set to `null` to turn off. Server VAD
              means that the model will detect the start and end of speech based on audio
              volume and respond at the end of user speech.

          voice: The voice the model uses to respond. Voice cannot be changed during the session
              once the model has responded with audio at least once. Current voice options are
              `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, and `verse`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/realtime/sessions",
            body=maybe_transform(
                {
                    "client_secret": client_secret,
                    "input_audio_format": input_audio_format,
                    "input_audio_transcription": input_audio_transcription,
                    "instructions": instructions,
                    "max_response_output_tokens": max_response_output_tokens,
                    "modalities": modalities,
                    "output_audio_format": output_audio_format,
                    "prompt": prompt,
                    "speed": speed,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "tracing": tracing,
                    "truncation": truncation,
                    "turn_detection": turn_detection,
                    "voice": voice,
                },
                realtime_create_session_params.RealtimeCreateSessionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateSessionResponse,
        )

    def create_transcription_session(
        self,
        *,
        include: List[Literal["item.input_audio_transcription.logprobs"]] | Omit = omit,
        input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | Omit = omit,
        input_audio_noise_reduction: realtime_create_transcription_session_params.InputAudioNoiseReduction
        | Omit = omit,
        input_audio_transcription: AudioTranscriptionParam | Omit = omit,
        turn_detection: realtime_create_transcription_session_params.TurnDetection | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateTranscriptionSessionResponse:
        """
        Create an ephemeral API token for use in client-side applications with the
        Realtime API specifically for realtime transcriptions. Can be configured with
        the same session parameters as the `transcription_session.update` client event.

        It responds with a session object, plus a `client_secret` key which contains a
        usable ephemeral API token that can be used to authenticate browser clients for
        the Realtime API.

        Args:
          include:
              The set of items to include in the transcription. Current available items are:
              `item.input_audio_transcription.logprobs`

          input_audio_format: The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`. For
              `pcm16`, input audio must be 16-bit PCM at a 24kHz sample rate, single channel
              (mono), and little-endian byte order.

          input_audio_noise_reduction: Configuration for input audio noise reduction. This can be set to `null` to turn
              off. Noise reduction filters audio added to the input audio buffer before it is
              sent to VAD and the model. Filtering the audio can improve VAD and turn
              detection accuracy (reducing false positives) and model performance by improving
              perception of the input audio.

          input_audio_transcription: Configuration for input audio transcription. The client can optionally set the
              language and prompt for transcription, these offer additional guidance to the
              transcription service.

          turn_detection: Configuration for turn detection. Can be set to `null` to turn off. Server VAD
              means that the model will detect the start and end of speech based on audio
              volume and respond at the end of user speech.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/realtime/transcription_sessions",
            body=maybe_transform(
                {
                    "include": include,
                    "input_audio_format": input_audio_format,
                    "input_audio_noise_reduction": input_audio_noise_reduction,
                    "input_audio_transcription": input_audio_transcription,
                    "turn_detection": turn_detection,
                },
                realtime_create_transcription_session_params.RealtimeCreateTranscriptionSessionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateTranscriptionSessionResponse,
        )


class AsyncRealtimeResource(AsyncAPIResource):
    @cached_property
    def calls(self) -> AsyncCallsResource:
        return AsyncCallsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRealtimeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRealtimeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRealtimeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncRealtimeResourceWithStreamingResponse(self)

    async def create_client_secret(
        self,
        *,
        expires_after: realtime_create_client_secret_params.ExpiresAfter | Omit = omit,
        session: realtime_create_client_secret_params.Session | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateClientSecretResponse:
        """
        Create a Realtime client secret with an associated session configuration.

        Args:
          expires_after: Configuration for the client secret expiration. Expiration refers to the time
              after which a client secret will no longer be valid for creating sessions. The
              session itself may continue after that time once started. A secret can be used
              to create multiple sessions until it expires.

          session: Session configuration to use for the client secret. Choose either a realtime
              session or a transcription session.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/realtime/client_secrets",
            body=await async_maybe_transform(
                {
                    "expires_after": expires_after,
                    "session": session,
                },
                realtime_create_client_secret_params.RealtimeCreateClientSecretParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateClientSecretResponse,
        )

    async def create_session(
        self,
        *,
        client_secret: realtime_create_session_params.ClientSecret,
        input_audio_format: str | Omit = omit,
        input_audio_transcription: realtime_create_session_params.InputAudioTranscription | Omit = omit,
        instructions: str | Omit = omit,
        max_response_output_tokens: Union[int, Literal["inf"]] | Omit = omit,
        modalities: List[Literal["text", "audio"]] | Omit = omit,
        output_audio_format: str | Omit = omit,
        prompt: Optional[PromptParam] | Omit = omit,
        speed: float | Omit = omit,
        temperature: float | Omit = omit,
        tool_choice: str | Omit = omit,
        tools: Iterable[realtime_create_session_params.Tool] | Omit = omit,
        tracing: realtime_create_session_params.Tracing | Omit = omit,
        truncation: RealtimeTruncationParam | Omit = omit,
        turn_detection: realtime_create_session_params.TurnDetection | Omit = omit,
        voice: VoiceIDsSharedParam | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateSessionResponse:
        """
        Create an ephemeral API token for use in client-side applications with the
        Realtime API. Can be configured with the same session parameters as the
        `session.update` client event.

        It responds with a session object, plus a `client_secret` key which contains a
        usable ephemeral API token that can be used to authenticate browser clients for
        the Realtime API.

        Args:
          client_secret: Ephemeral key returned by the API.

          input_audio_format: The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`.

          input_audio_transcription: Configuration for input audio transcription, defaults to off and can be set to
              `null` to turn off once on. Input audio transcription is not native to the
              model, since the model consumes audio directly. Transcription runs
              asynchronously and should be treated as rough guidance rather than the
              representation understood by the model.

          instructions: The default system instructions (i.e. system message) prepended to model calls.
              This field allows the client to guide the model on desired responses. The model
              can be instructed on response content and format, (e.g. "be extremely succinct",
              "act friendly", "here are examples of good responses") and on audio behavior
              (e.g. "talk quickly", "inject emotion into your voice", "laugh frequently"). The
              instructions are not guaranteed to be followed by the model, but they provide
              guidance to the model on the desired behavior. Note that the server sets default
              instructions which will be used if this field is not set and are visible in the
              `session.created` event at the start of the session.

          max_response_output_tokens: Maximum number of output tokens for a single assistant response, inclusive of
              tool calls. Provide an integer between 1 and 4096 to limit output tokens, or
              `inf` for the maximum available tokens for a given model. Defaults to `inf`.

          modalities: The set of modalities the model can respond with. To disable audio, set this to
              ["text"].

          output_audio_format: The format of output audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`.

          prompt: Reference to a prompt template and its variables.
              [Learn more](https://main.excai.ai/docs/guides/text?api-mode=responses#reusable-prompts).

          speed: The speed of the model's spoken response. 1.0 is the default speed. 0.25 is the
              minimum speed. 1.5 is the maximum speed. This value can only be changed in
              between model turns, not while a response is in progress.

          temperature: Sampling temperature for the model, limited to [0.6, 1.2]. Defaults to 0.8.

          tool_choice: How the model chooses tools. Options are `auto`, `none`, `required`, or specify
              a function.

          tools: Tools (functions) available to the model.

          tracing: Configuration options for tracing. Set to null to disable tracing. Once tracing
              is enabled for a session, the configuration cannot be modified.

              `auto` will create a trace for the session with default values for the workflow
              name, group id, and metadata.

          truncation: Controls how the realtime conversation is truncated prior to model inference.
              The default is `auto`.

          turn_detection: Configuration for turn detection. Can be set to `null` to turn off. Server VAD
              means that the model will detect the start and end of speech based on audio
              volume and respond at the end of user speech.

          voice: The voice the model uses to respond. Voice cannot be changed during the session
              once the model has responded with audio at least once. Current voice options are
              `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, and `verse`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/realtime/sessions",
            body=await async_maybe_transform(
                {
                    "client_secret": client_secret,
                    "input_audio_format": input_audio_format,
                    "input_audio_transcription": input_audio_transcription,
                    "instructions": instructions,
                    "max_response_output_tokens": max_response_output_tokens,
                    "modalities": modalities,
                    "output_audio_format": output_audio_format,
                    "prompt": prompt,
                    "speed": speed,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "tracing": tracing,
                    "truncation": truncation,
                    "turn_detection": turn_detection,
                    "voice": voice,
                },
                realtime_create_session_params.RealtimeCreateSessionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateSessionResponse,
        )

    async def create_transcription_session(
        self,
        *,
        include: List[Literal["item.input_audio_transcription.logprobs"]] | Omit = omit,
        input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] | Omit = omit,
        input_audio_noise_reduction: realtime_create_transcription_session_params.InputAudioNoiseReduction
        | Omit = omit,
        input_audio_transcription: AudioTranscriptionParam | Omit = omit,
        turn_detection: realtime_create_transcription_session_params.TurnDetection | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RealtimeCreateTranscriptionSessionResponse:
        """
        Create an ephemeral API token for use in client-side applications with the
        Realtime API specifically for realtime transcriptions. Can be configured with
        the same session parameters as the `transcription_session.update` client event.

        It responds with a session object, plus a `client_secret` key which contains a
        usable ephemeral API token that can be used to authenticate browser clients for
        the Realtime API.

        Args:
          include:
              The set of items to include in the transcription. Current available items are:
              `item.input_audio_transcription.logprobs`

          input_audio_format: The format of input audio. Options are `pcm16`, `g711_ulaw`, or `g711_alaw`. For
              `pcm16`, input audio must be 16-bit PCM at a 24kHz sample rate, single channel
              (mono), and little-endian byte order.

          input_audio_noise_reduction: Configuration for input audio noise reduction. This can be set to `null` to turn
              off. Noise reduction filters audio added to the input audio buffer before it is
              sent to VAD and the model. Filtering the audio can improve VAD and turn
              detection accuracy (reducing false positives) and model performance by improving
              perception of the input audio.

          input_audio_transcription: Configuration for input audio transcription. The client can optionally set the
              language and prompt for transcription, these offer additional guidance to the
              transcription service.

          turn_detection: Configuration for turn detection. Can be set to `null` to turn off. Server VAD
              means that the model will detect the start and end of speech based on audio
              volume and respond at the end of user speech.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/realtime/transcription_sessions",
            body=await async_maybe_transform(
                {
                    "include": include,
                    "input_audio_format": input_audio_format,
                    "input_audio_noise_reduction": input_audio_noise_reduction,
                    "input_audio_transcription": input_audio_transcription,
                    "turn_detection": turn_detection,
                },
                realtime_create_transcription_session_params.RealtimeCreateTranscriptionSessionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RealtimeCreateTranscriptionSessionResponse,
        )


class RealtimeResourceWithRawResponse:
    def __init__(self, realtime: RealtimeResource) -> None:
        self._realtime = realtime

        self.create_client_secret = to_raw_response_wrapper(
            realtime.create_client_secret,
        )
        self.create_session = to_raw_response_wrapper(
            realtime.create_session,
        )
        self.create_transcription_session = to_raw_response_wrapper(
            realtime.create_transcription_session,
        )

    @cached_property
    def calls(self) -> CallsResourceWithRawResponse:
        return CallsResourceWithRawResponse(self._realtime.calls)


class AsyncRealtimeResourceWithRawResponse:
    def __init__(self, realtime: AsyncRealtimeResource) -> None:
        self._realtime = realtime

        self.create_client_secret = async_to_raw_response_wrapper(
            realtime.create_client_secret,
        )
        self.create_session = async_to_raw_response_wrapper(
            realtime.create_session,
        )
        self.create_transcription_session = async_to_raw_response_wrapper(
            realtime.create_transcription_session,
        )

    @cached_property
    def calls(self) -> AsyncCallsResourceWithRawResponse:
        return AsyncCallsResourceWithRawResponse(self._realtime.calls)


class RealtimeResourceWithStreamingResponse:
    def __init__(self, realtime: RealtimeResource) -> None:
        self._realtime = realtime

        self.create_client_secret = to_streamed_response_wrapper(
            realtime.create_client_secret,
        )
        self.create_session = to_streamed_response_wrapper(
            realtime.create_session,
        )
        self.create_transcription_session = to_streamed_response_wrapper(
            realtime.create_transcription_session,
        )

    @cached_property
    def calls(self) -> CallsResourceWithStreamingResponse:
        return CallsResourceWithStreamingResponse(self._realtime.calls)


class AsyncRealtimeResourceWithStreamingResponse:
    def __init__(self, realtime: AsyncRealtimeResource) -> None:
        self._realtime = realtime

        self.create_client_secret = async_to_streamed_response_wrapper(
            realtime.create_client_secret,
        )
        self.create_session = async_to_streamed_response_wrapper(
            realtime.create_session,
        )
        self.create_transcription_session = async_to_streamed_response_wrapper(
            realtime.create_transcription_session,
        )

    @cached_property
    def calls(self) -> AsyncCallsResourceWithStreamingResponse:
        return AsyncCallsResourceWithStreamingResponse(self._realtime.calls)
