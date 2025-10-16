# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal

import httpx

from .steps import (
    StepsResource,
    AsyncStepsResource,
    StepsResourceWithRawResponse,
    AsyncStepsResourceWithRawResponse,
    StepsResourceWithStreamingResponse,
    AsyncStepsResourceWithStreamingResponse,
)
from ....types import ReasoningEffort
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.threads import (
    run_list_params,
    run_create_params,
    run_update_params,
    run_create_with_run_params,
    run_submit_tool_outputs_params,
)
from ....types.threads.run import Run
from ....types.reasoning_effort import ReasoningEffort
from ....types.chat.metadata_param import MetadataParam
from ....types.create_thread_param import CreateThreadParam
from ....types.threads.truncation_param import TruncationParam
from ....types.threads.run_list_response import RunListResponse
from ....types.assistant_supported_models import AssistantSupportedModels
from ....types.threads.create_message_param import CreateMessageParam
from ....types.threads.api_tool_choice_option_param import APIToolChoiceOptionParam
from ....types.threads.api_response_format_option_param import APIResponseFormatOptionParam

__all__ = ["RunsResource", "AsyncRunsResource"]


class RunsResource(SyncAPIResource):
    @cached_property
    def steps(self) -> StepsResource:
        return StepsResource(self._client)

    @cached_property
    def with_raw_response(self) -> RunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return RunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return RunsResourceWithStreamingResponse(self)

    def create(
        self,
        thread_id: str,
        *,
        assistant_id: str,
        include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] | Omit = omit,
        additional_instructions: Optional[str] | Omit = omit,
        additional_messages: Optional[Iterable[CreateMessageParam]] | Omit = omit,
        instructions: Optional[str] | Omit = omit,
        max_completion_tokens: Optional[int] | Omit = omit,
        max_prompt_tokens: Optional[int] | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: Union[str, AssistantSupportedModels, None] | Omit = omit,
        parallel_tool_calls: bool | Omit = omit,
        reasoning_effort: Optional[ReasoningEffort] | Omit = omit,
        response_format: Optional[APIResponseFormatOptionParam] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        tool_choice: Optional[APIToolChoiceOptionParam] | Omit = omit,
        tools: Optional[Iterable[run_create_params.Tool]] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
        truncation_strategy: Optional[TruncationParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Create a run.

        Args:
          assistant_id: The ID of the [assistant](https://main.excai.ai/docs/api-reference/assistants)
              to use to execute this run.

          include: A list of additional fields to include in the response. Currently the only
              supported value is `step_details.tool_calls[*].file_search.results[*].content`
              to fetch the file search result content.

              See the
              [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
              for more information.

          additional_instructions: Appends additional instructions at the end of the instructions for the run. This
              is useful for modifying the behavior on a per-run basis without overriding other
              instructions.

          additional_messages: Adds additional messages to the thread before creating the run.

          instructions: Overrides the
              [instructions](https://main.excai.ai/docs/api-reference/assistants/createAssistant)
              of the assistant. This is useful for modifying the behavior on a per-run basis.

          max_completion_tokens: The maximum number of completion tokens that may be used over the course of the
              run. The run will make a best effort to use only the number of completion tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              completion tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          max_prompt_tokens: The maximum number of prompt tokens that may be used over the course of the run.
              The run will make a best effort to use only the number of prompt tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              prompt tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The ID of the [Model](https://main.excai.ai/docs/api-reference/models) to be
              used to execute this run. If a value is provided here, it will override the
              model associated with the assistant. If not, the model associated with the
              assistant will be used.

          parallel_tool_calls: Whether to enable
              [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
              during tool use.

          reasoning_effort: Constrains effort on reasoning for
              [reasoning models](https://main.excai.ai/docs/guides/reasoning). Currently
              supported values are `minimal`, `low`, `medium`, and `high`. Reducing reasoning
              effort can result in faster responses and fewer tokens used on reasoning in a
              response.

              Note: The `gpt-5-pro` model defaults to (and only supports) `high` reasoning
              effort.

          response_format: Specifies the format that the model must output. Compatible with
              [openai/gpt-oss-120b](https://main.excai.ai/docs/models#openai/gpt-oss-120b),
              [GPT-4 Turbo](https://main.excai.ai/docs/models#gpt-4-turbo-and-gpt-4), and all
              GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

              Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
              Outputs which ensures the model will match your supplied JSON schema. Learn more
              in the
              [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

              Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
              message the model generates is valid JSON.

              **Important:** when using JSON mode, you **must** also instruct the model to
              produce JSON yourself via a system or user message. Without this, the model may
              generate an unending stream of whitespace until the generation reaches the token
              limit, resulting in a long-running and seemingly "stuck" request. Also note that
              the message content may be partially cut off if `finish_reason="length"`, which
              indicates the generation exceeded `max_tokens` or the conversation exceeded the
              max context length.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
              make the output more random, while lower values like 0.2 will make it more
              focused and deterministic.

          tool_choice: Controls which (if any) tool is called by the model. `none` means the model will
              not call any tools and instead generates a message. `auto` is the default value
              and means the model can pick between generating a message or calling one or more
              tools. `required` means the model must call one or more tools before responding
              to the user. Specifying a particular tool like `{"type": "file_search"}` or
              `{"type": "function", "function": {"name": "my_function"}}` forces the model to
              call that tool.

          tools: Override the tools the assistant can use for this run. This is useful for
              modifying the behavior on a per-run basis.

          top_p: An alternative to sampling with temperature, called nucleus sampling, where the
              model considers the results of the tokens with top_p probability mass. So 0.1
              means only the tokens comprising the top 10% probability mass are considered.

              We generally recommend altering this or temperature but not both.

          truncation_strategy: Controls for how a thread will be truncated prior to the run. Use this to
              control the initial context window of the run.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        return self._post(
            f"/threads/{thread_id}/runs",
            body=maybe_transform(
                {
                    "assistant_id": assistant_id,
                    "additional_instructions": additional_instructions,
                    "additional_messages": additional_messages,
                    "instructions": instructions,
                    "max_completion_tokens": max_completion_tokens,
                    "max_prompt_tokens": max_prompt_tokens,
                    "metadata": metadata,
                    "model": model,
                    "parallel_tool_calls": parallel_tool_calls,
                    "reasoning_effort": reasoning_effort,
                    "response_format": response_format,
                    "stream": stream,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_p": top_p,
                    "truncation_strategy": truncation_strategy,
                },
                run_create_params.RunCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"include": include}, run_create_params.RunCreateParams),
            ),
            cast_to=Run,
        )

    def retrieve(
        self,
        run_id: str,
        *,
        thread_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Retrieves a run.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._get(
            f"/threads/{thread_id}/runs/{run_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    def update(
        self,
        run_id: str,
        *,
        thread_id: str,
        metadata: Optional[MetadataParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Modifies a run.

        Args:
          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._post(
            f"/threads/{thread_id}/runs/{run_id}",
            body=maybe_transform({"metadata": metadata}, run_update_params.RunUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    def list(
        self,
        thread_id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunListResponse:
        """
        Returns a list of runs belonging to a thread.

        Args:
          after: A cursor for use in pagination. `after` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              ending with obj_foo, your subsequent call can include after=obj_foo in order to
              fetch the next page of the list.

          before: A cursor for use in pagination. `before` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              starting with obj_foo, your subsequent call can include before=obj_foo in order
              to fetch the previous page of the list.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: Sort order by the `created_at` timestamp of the objects. `asc` for ascending
              order and `desc` for descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        return self._get(
            f"/threads/{thread_id}/runs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "limit": limit,
                        "order": order,
                    },
                    run_list_params.RunListParams,
                ),
            ),
            cast_to=RunListResponse,
        )

    def cancel(
        self,
        run_id: str,
        *,
        thread_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Cancels a run that is `in_progress`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._post(
            f"/threads/{thread_id}/runs/{run_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    def create_with_run(
        self,
        *,
        assistant_id: str,
        instructions: Optional[str] | Omit = omit,
        max_completion_tokens: Optional[int] | Omit = omit,
        max_prompt_tokens: Optional[int] | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: Union[
            str,
            Literal[
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-5-2025-08-07",
                "gpt-5-mini-2025-08-07",
                "gpt-5-nano-2025-08-07",
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                "gpt-4.1-2025-04-14",
                "gpt-4.1-mini-2025-04-14",
                "gpt-4.1-nano-2025-04-14",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-120b-2024-11-20",
                "openai/gpt-oss-120b-2024-08-06",
                "openai/gpt-oss-120b-2024-05-13",
                "openai/gpt-oss-120b-2024-07-18",
                "gpt-4.5-preview",
                "gpt-4.5-preview-2025-02-27",
                "gpt-4-turbo",
                "gpt-4-turbo-2024-04-09",
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-4-1106-preview",
                "gpt-4-vision-preview",
                "gpt-4",
                "gpt-4-0314",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0314",
                "gpt-4-32k-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-1106",
                "gpt-3.5-turbo-0125",
                "gpt-3.5-turbo-16k-0613",
            ],
            None,
        ]
        | Omit = omit,
        parallel_tool_calls: bool | Omit = omit,
        response_format: Optional[APIResponseFormatOptionParam] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        thread: CreateThreadParam | Omit = omit,
        tool_choice: Optional[APIToolChoiceOptionParam] | Omit = omit,
        tool_resources: Optional[run_create_with_run_params.ToolResources] | Omit = omit,
        tools: Optional[Iterable[run_create_with_run_params.Tool]] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
        truncation_strategy: Optional[TruncationParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Create a thread and run it in one request.

        Args:
          assistant_id: The ID of the [assistant](https://main.excai.ai/docs/api-reference/assistants)
              to use to execute this run.

          instructions: Override the default system message of the assistant. This is useful for
              modifying the behavior on a per-run basis.

          max_completion_tokens: The maximum number of completion tokens that may be used over the course of the
              run. The run will make a best effort to use only the number of completion tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              completion tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          max_prompt_tokens: The maximum number of prompt tokens that may be used over the course of the run.
              The run will make a best effort to use only the number of prompt tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              prompt tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The ID of the [Model](https://main.excai.ai/docs/api-reference/models) to be
              used to execute this run. If a value is provided here, it will override the
              model associated with the assistant. If not, the model associated with the
              assistant will be used.

          parallel_tool_calls: Whether to enable
              [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
              during tool use.

          response_format: Specifies the format that the model must output. Compatible with
              [openai/gpt-oss-120b](https://main.excai.ai/docs/models#openai/gpt-oss-120b),
              [GPT-4 Turbo](https://main.excai.ai/docs/models#gpt-4-turbo-and-gpt-4), and all
              GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

              Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
              Outputs which ensures the model will match your supplied JSON schema. Learn more
              in the
              [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

              Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
              message the model generates is valid JSON.

              **Important:** when using JSON mode, you **must** also instruct the model to
              produce JSON yourself via a system or user message. Without this, the model may
              generate an unending stream of whitespace until the generation reaches the token
              limit, resulting in a long-running and seemingly "stuck" request. Also note that
              the message content may be partially cut off if `finish_reason="length"`, which
              indicates the generation exceeded `max_tokens` or the conversation exceeded the
              max context length.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
              make the output more random, while lower values like 0.2 will make it more
              focused and deterministic.

          thread: Options to create a new thread. If no thread is provided when running a request,
              an empty thread will be created.

          tool_choice: Controls which (if any) tool is called by the model. `none` means the model will
              not call any tools and instead generates a message. `auto` is the default value
              and means the model can pick between generating a message or calling one or more
              tools. `required` means the model must call one or more tools before responding
              to the user. Specifying a particular tool like `{"type": "file_search"}` or
              `{"type": "function", "function": {"name": "my_function"}}` forces the model to
              call that tool.

          tool_resources: A set of resources that are used by the assistant's tools. The resources are
              specific to the type of tool. For example, the `code_interpreter` tool requires
              a list of file IDs, while the `file_search` tool requires a list of vector store
              IDs.

          tools: Override the tools the assistant can use for this run. This is useful for
              modifying the behavior on a per-run basis.

          top_p: An alternative to sampling with temperature, called nucleus sampling, where the
              model considers the results of the tokens with top_p probability mass. So 0.1
              means only the tokens comprising the top 10% probability mass are considered.

              We generally recommend altering this or temperature but not both.

          truncation_strategy: Controls for how a thread will be truncated prior to the run. Use this to
              control the initial context window of the run.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/threads/runs",
            body=maybe_transform(
                {
                    "assistant_id": assistant_id,
                    "instructions": instructions,
                    "max_completion_tokens": max_completion_tokens,
                    "max_prompt_tokens": max_prompt_tokens,
                    "metadata": metadata,
                    "model": model,
                    "parallel_tool_calls": parallel_tool_calls,
                    "response_format": response_format,
                    "stream": stream,
                    "temperature": temperature,
                    "thread": thread,
                    "tool_choice": tool_choice,
                    "tool_resources": tool_resources,
                    "tools": tools,
                    "top_p": top_p,
                    "truncation_strategy": truncation_strategy,
                },
                run_create_with_run_params.RunCreateWithRunParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    def submit_tool_outputs(
        self,
        run_id: str,
        *,
        thread_id: str,
        tool_outputs: Iterable[run_submit_tool_outputs_params.ToolOutput],
        stream: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        When a run has the `status: "requires_action"` and `required_action.type` is
        `submit_tool_outputs`, this endpoint can be used to submit the outputs from the
        tool calls once they're all completed. All outputs must be submitted in a single
        request.

        Args:
          tool_outputs: A list of tools for which the outputs are being submitted.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return self._post(
            f"/threads/{thread_id}/runs/{run_id}/submit_tool_outputs",
            body=maybe_transform(
                {
                    "tool_outputs": tool_outputs,
                    "stream": stream,
                },
                run_submit_tool_outputs_params.RunSubmitToolOutputsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )


class AsyncRunsResource(AsyncAPIResource):
    @cached_property
    def steps(self) -> AsyncStepsResource:
        return AsyncStepsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRunsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRunsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRunsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncRunsResourceWithStreamingResponse(self)

    async def create(
        self,
        thread_id: str,
        *,
        assistant_id: str,
        include: List[Literal["step_details.tool_calls[*].file_search.results[*].content"]] | Omit = omit,
        additional_instructions: Optional[str] | Omit = omit,
        additional_messages: Optional[Iterable[CreateMessageParam]] | Omit = omit,
        instructions: Optional[str] | Omit = omit,
        max_completion_tokens: Optional[int] | Omit = omit,
        max_prompt_tokens: Optional[int] | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: Union[str, AssistantSupportedModels, None] | Omit = omit,
        parallel_tool_calls: bool | Omit = omit,
        reasoning_effort: Optional[ReasoningEffort] | Omit = omit,
        response_format: Optional[APIResponseFormatOptionParam] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        tool_choice: Optional[APIToolChoiceOptionParam] | Omit = omit,
        tools: Optional[Iterable[run_create_params.Tool]] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
        truncation_strategy: Optional[TruncationParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Create a run.

        Args:
          assistant_id: The ID of the [assistant](https://main.excai.ai/docs/api-reference/assistants)
              to use to execute this run.

          include: A list of additional fields to include in the response. Currently the only
              supported value is `step_details.tool_calls[*].file_search.results[*].content`
              to fetch the file search result content.

              See the
              [file search tool documentation](https://main.excai.ai/docs/assistants/tools/file-search#customizing-file-search-settings)
              for more information.

          additional_instructions: Appends additional instructions at the end of the instructions for the run. This
              is useful for modifying the behavior on a per-run basis without overriding other
              instructions.

          additional_messages: Adds additional messages to the thread before creating the run.

          instructions: Overrides the
              [instructions](https://main.excai.ai/docs/api-reference/assistants/createAssistant)
              of the assistant. This is useful for modifying the behavior on a per-run basis.

          max_completion_tokens: The maximum number of completion tokens that may be used over the course of the
              run. The run will make a best effort to use only the number of completion tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              completion tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          max_prompt_tokens: The maximum number of prompt tokens that may be used over the course of the run.
              The run will make a best effort to use only the number of prompt tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              prompt tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The ID of the [Model](https://main.excai.ai/docs/api-reference/models) to be
              used to execute this run. If a value is provided here, it will override the
              model associated with the assistant. If not, the model associated with the
              assistant will be used.

          parallel_tool_calls: Whether to enable
              [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
              during tool use.

          reasoning_effort: Constrains effort on reasoning for
              [reasoning models](https://main.excai.ai/docs/guides/reasoning). Currently
              supported values are `minimal`, `low`, `medium`, and `high`. Reducing reasoning
              effort can result in faster responses and fewer tokens used on reasoning in a
              response.

              Note: The `gpt-5-pro` model defaults to (and only supports) `high` reasoning
              effort.

          response_format: Specifies the format that the model must output. Compatible with
              [openai/gpt-oss-120b](https://main.excai.ai/docs/models#openai/gpt-oss-120b),
              [GPT-4 Turbo](https://main.excai.ai/docs/models#gpt-4-turbo-and-gpt-4), and all
              GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

              Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
              Outputs which ensures the model will match your supplied JSON schema. Learn more
              in the
              [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

              Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
              message the model generates is valid JSON.

              **Important:** when using JSON mode, you **must** also instruct the model to
              produce JSON yourself via a system or user message. Without this, the model may
              generate an unending stream of whitespace until the generation reaches the token
              limit, resulting in a long-running and seemingly "stuck" request. Also note that
              the message content may be partially cut off if `finish_reason="length"`, which
              indicates the generation exceeded `max_tokens` or the conversation exceeded the
              max context length.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
              make the output more random, while lower values like 0.2 will make it more
              focused and deterministic.

          tool_choice: Controls which (if any) tool is called by the model. `none` means the model will
              not call any tools and instead generates a message. `auto` is the default value
              and means the model can pick between generating a message or calling one or more
              tools. `required` means the model must call one or more tools before responding
              to the user. Specifying a particular tool like `{"type": "file_search"}` or
              `{"type": "function", "function": {"name": "my_function"}}` forces the model to
              call that tool.

          tools: Override the tools the assistant can use for this run. This is useful for
              modifying the behavior on a per-run basis.

          top_p: An alternative to sampling with temperature, called nucleus sampling, where the
              model considers the results of the tokens with top_p probability mass. So 0.1
              means only the tokens comprising the top 10% probability mass are considered.

              We generally recommend altering this or temperature but not both.

          truncation_strategy: Controls for how a thread will be truncated prior to the run. Use this to
              control the initial context window of the run.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        return await self._post(
            f"/threads/{thread_id}/runs",
            body=await async_maybe_transform(
                {
                    "assistant_id": assistant_id,
                    "additional_instructions": additional_instructions,
                    "additional_messages": additional_messages,
                    "instructions": instructions,
                    "max_completion_tokens": max_completion_tokens,
                    "max_prompt_tokens": max_prompt_tokens,
                    "metadata": metadata,
                    "model": model,
                    "parallel_tool_calls": parallel_tool_calls,
                    "reasoning_effort": reasoning_effort,
                    "response_format": response_format,
                    "stream": stream,
                    "temperature": temperature,
                    "tool_choice": tool_choice,
                    "tools": tools,
                    "top_p": top_p,
                    "truncation_strategy": truncation_strategy,
                },
                run_create_params.RunCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"include": include}, run_create_params.RunCreateParams),
            ),
            cast_to=Run,
        )

    async def retrieve(
        self,
        run_id: str,
        *,
        thread_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Retrieves a run.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._get(
            f"/threads/{thread_id}/runs/{run_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    async def update(
        self,
        run_id: str,
        *,
        thread_id: str,
        metadata: Optional[MetadataParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Modifies a run.

        Args:
          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._post(
            f"/threads/{thread_id}/runs/{run_id}",
            body=await async_maybe_transform({"metadata": metadata}, run_update_params.RunUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    async def list(
        self,
        thread_id: str,
        *,
        after: str | Omit = omit,
        before: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RunListResponse:
        """
        Returns a list of runs belonging to a thread.

        Args:
          after: A cursor for use in pagination. `after` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              ending with obj_foo, your subsequent call can include after=obj_foo in order to
              fetch the next page of the list.

          before: A cursor for use in pagination. `before` is an object ID that defines your place
              in the list. For instance, if you make a list request and receive 100 objects,
              starting with obj_foo, your subsequent call can include before=obj_foo in order
              to fetch the previous page of the list.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: Sort order by the `created_at` timestamp of the objects. `asc` for ascending
              order and `desc` for descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        return await self._get(
            f"/threads/{thread_id}/runs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "limit": limit,
                        "order": order,
                    },
                    run_list_params.RunListParams,
                ),
            ),
            cast_to=RunListResponse,
        )

    async def cancel(
        self,
        run_id: str,
        *,
        thread_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Cancels a run that is `in_progress`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._post(
            f"/threads/{thread_id}/runs/{run_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    async def create_with_run(
        self,
        *,
        assistant_id: str,
        instructions: Optional[str] | Omit = omit,
        max_completion_tokens: Optional[int] | Omit = omit,
        max_prompt_tokens: Optional[int] | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: Union[
            str,
            Literal[
                "gpt-5",
                "gpt-5-mini",
                "gpt-5-nano",
                "gpt-5-2025-08-07",
                "gpt-5-mini-2025-08-07",
                "gpt-5-nano-2025-08-07",
                "gpt-4.1",
                "gpt-4.1-mini",
                "gpt-4.1-nano",
                "gpt-4.1-2025-04-14",
                "gpt-4.1-mini-2025-04-14",
                "gpt-4.1-nano-2025-04-14",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-120b-2024-11-20",
                "openai/gpt-oss-120b-2024-08-06",
                "openai/gpt-oss-120b-2024-05-13",
                "openai/gpt-oss-120b-2024-07-18",
                "gpt-4.5-preview",
                "gpt-4.5-preview-2025-02-27",
                "gpt-4-turbo",
                "gpt-4-turbo-2024-04-09",
                "gpt-4-0125-preview",
                "gpt-4-turbo-preview",
                "gpt-4-1106-preview",
                "gpt-4-vision-preview",
                "gpt-4",
                "gpt-4-0314",
                "gpt-4-0613",
                "gpt-4-32k",
                "gpt-4-32k-0314",
                "gpt-4-32k-0613",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-3.5-turbo-0613",
                "gpt-3.5-turbo-1106",
                "gpt-3.5-turbo-0125",
                "gpt-3.5-turbo-16k-0613",
            ],
            None,
        ]
        | Omit = omit,
        parallel_tool_calls: bool | Omit = omit,
        response_format: Optional[APIResponseFormatOptionParam] | Omit = omit,
        stream: Optional[bool] | Omit = omit,
        temperature: Optional[float] | Omit = omit,
        thread: CreateThreadParam | Omit = omit,
        tool_choice: Optional[APIToolChoiceOptionParam] | Omit = omit,
        tool_resources: Optional[run_create_with_run_params.ToolResources] | Omit = omit,
        tools: Optional[Iterable[run_create_with_run_params.Tool]] | Omit = omit,
        top_p: Optional[float] | Omit = omit,
        truncation_strategy: Optional[TruncationParam] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        Create a thread and run it in one request.

        Args:
          assistant_id: The ID of the [assistant](https://main.excai.ai/docs/api-reference/assistants)
              to use to execute this run.

          instructions: Override the default system message of the assistant. This is useful for
              modifying the behavior on a per-run basis.

          max_completion_tokens: The maximum number of completion tokens that may be used over the course of the
              run. The run will make a best effort to use only the number of completion tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              completion tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          max_prompt_tokens: The maximum number of prompt tokens that may be used over the course of the run.
              The run will make a best effort to use only the number of prompt tokens
              specified, across multiple turns of the run. If the run exceeds the number of
              prompt tokens specified, the run will end with status `incomplete`. See
              `incomplete_details` for more info.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The ID of the [Model](https://main.excai.ai/docs/api-reference/models) to be
              used to execute this run. If a value is provided here, it will override the
              model associated with the assistant. If not, the model associated with the
              assistant will be used.

          parallel_tool_calls: Whether to enable
              [parallel function calling](https://main.excai.ai/docs/guides/function-calling#configuring-parallel-function-calling)
              during tool use.

          response_format: Specifies the format that the model must output. Compatible with
              [openai/gpt-oss-120b](https://main.excai.ai/docs/models#openai/gpt-oss-120b),
              [GPT-4 Turbo](https://main.excai.ai/docs/models#gpt-4-turbo-and-gpt-4), and all
              GPT-3.5 Turbo models since `gpt-3.5-turbo-1106`.

              Setting to `{ "type": "json_schema", "json_schema": {...} }` enables Structured
              Outputs which ensures the model will match your supplied JSON schema. Learn more
              in the
              [Structured Outputs guide](https://main.excai.ai/docs/guides/structured-outputs).

              Setting to `{ "type": "json_object" }` enables JSON mode, which ensures the
              message the model generates is valid JSON.

              **Important:** when using JSON mode, you **must** also instruct the model to
              produce JSON yourself via a system or user message. Without this, the model may
              generate an unending stream of whitespace until the generation reaches the token
              limit, resulting in a long-running and seemingly "stuck" request. Also note that
              the message content may be partially cut off if `finish_reason="length"`, which
              indicates the generation exceeded `max_tokens` or the conversation exceeded the
              max context length.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          temperature: What sampling temperature to use, between 0 and 2. Higher values like 0.8 will
              make the output more random, while lower values like 0.2 will make it more
              focused and deterministic.

          thread: Options to create a new thread. If no thread is provided when running a request,
              an empty thread will be created.

          tool_choice: Controls which (if any) tool is called by the model. `none` means the model will
              not call any tools and instead generates a message. `auto` is the default value
              and means the model can pick between generating a message or calling one or more
              tools. `required` means the model must call one or more tools before responding
              to the user. Specifying a particular tool like `{"type": "file_search"}` or
              `{"type": "function", "function": {"name": "my_function"}}` forces the model to
              call that tool.

          tool_resources: A set of resources that are used by the assistant's tools. The resources are
              specific to the type of tool. For example, the `code_interpreter` tool requires
              a list of file IDs, while the `file_search` tool requires a list of vector store
              IDs.

          tools: Override the tools the assistant can use for this run. This is useful for
              modifying the behavior on a per-run basis.

          top_p: An alternative to sampling with temperature, called nucleus sampling, where the
              model considers the results of the tokens with top_p probability mass. So 0.1
              means only the tokens comprising the top 10% probability mass are considered.

              We generally recommend altering this or temperature but not both.

          truncation_strategy: Controls for how a thread will be truncated prior to the run. Use this to
              control the initial context window of the run.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/threads/runs",
            body=await async_maybe_transform(
                {
                    "assistant_id": assistant_id,
                    "instructions": instructions,
                    "max_completion_tokens": max_completion_tokens,
                    "max_prompt_tokens": max_prompt_tokens,
                    "metadata": metadata,
                    "model": model,
                    "parallel_tool_calls": parallel_tool_calls,
                    "response_format": response_format,
                    "stream": stream,
                    "temperature": temperature,
                    "thread": thread,
                    "tool_choice": tool_choice,
                    "tool_resources": tool_resources,
                    "tools": tools,
                    "top_p": top_p,
                    "truncation_strategy": truncation_strategy,
                },
                run_create_with_run_params.RunCreateWithRunParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )

    async def submit_tool_outputs(
        self,
        run_id: str,
        *,
        thread_id: str,
        tool_outputs: Iterable[run_submit_tool_outputs_params.ToolOutput],
        stream: Optional[bool] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Run:
        """
        When a run has the `status: "requires_action"` and `required_action.type` is
        `submit_tool_outputs`, this endpoint can be used to submit the outputs from the
        tool calls once they're all completed. All outputs must be submitted in a single
        request.

        Args:
          tool_outputs: A list of tools for which the outputs are being submitted.

          stream: If `true`, returns a stream of events that happen during the Run as server-sent
              events, terminating when the Run enters a terminal state with a `data: [DONE]`
              message.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not thread_id:
            raise ValueError(f"Expected a non-empty value for `thread_id` but received {thread_id!r}")
        if not run_id:
            raise ValueError(f"Expected a non-empty value for `run_id` but received {run_id!r}")
        return await self._post(
            f"/threads/{thread_id}/runs/{run_id}/submit_tool_outputs",
            body=await async_maybe_transform(
                {
                    "tool_outputs": tool_outputs,
                    "stream": stream,
                },
                run_submit_tool_outputs_params.RunSubmitToolOutputsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Run,
        )


class RunsResourceWithRawResponse:
    def __init__(self, runs: RunsResource) -> None:
        self._runs = runs

        self.create = to_raw_response_wrapper(
            runs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            runs.retrieve,
        )
        self.update = to_raw_response_wrapper(
            runs.update,
        )
        self.list = to_raw_response_wrapper(
            runs.list,
        )
        self.cancel = to_raw_response_wrapper(
            runs.cancel,
        )
        self.create_with_run = to_raw_response_wrapper(
            runs.create_with_run,
        )
        self.submit_tool_outputs = to_raw_response_wrapper(
            runs.submit_tool_outputs,
        )

    @cached_property
    def steps(self) -> StepsResourceWithRawResponse:
        return StepsResourceWithRawResponse(self._runs.steps)


class AsyncRunsResourceWithRawResponse:
    def __init__(self, runs: AsyncRunsResource) -> None:
        self._runs = runs

        self.create = async_to_raw_response_wrapper(
            runs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            runs.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            runs.update,
        )
        self.list = async_to_raw_response_wrapper(
            runs.list,
        )
        self.cancel = async_to_raw_response_wrapper(
            runs.cancel,
        )
        self.create_with_run = async_to_raw_response_wrapper(
            runs.create_with_run,
        )
        self.submit_tool_outputs = async_to_raw_response_wrapper(
            runs.submit_tool_outputs,
        )

    @cached_property
    def steps(self) -> AsyncStepsResourceWithRawResponse:
        return AsyncStepsResourceWithRawResponse(self._runs.steps)


class RunsResourceWithStreamingResponse:
    def __init__(self, runs: RunsResource) -> None:
        self._runs = runs

        self.create = to_streamed_response_wrapper(
            runs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            runs.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            runs.update,
        )
        self.list = to_streamed_response_wrapper(
            runs.list,
        )
        self.cancel = to_streamed_response_wrapper(
            runs.cancel,
        )
        self.create_with_run = to_streamed_response_wrapper(
            runs.create_with_run,
        )
        self.submit_tool_outputs = to_streamed_response_wrapper(
            runs.submit_tool_outputs,
        )

    @cached_property
    def steps(self) -> StepsResourceWithStreamingResponse:
        return StepsResourceWithStreamingResponse(self._runs.steps)


class AsyncRunsResourceWithStreamingResponse:
    def __init__(self, runs: AsyncRunsResource) -> None:
        self._runs = runs

        self.create = async_to_streamed_response_wrapper(
            runs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            runs.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            runs.update,
        )
        self.list = async_to_streamed_response_wrapper(
            runs.list,
        )
        self.cancel = async_to_streamed_response_wrapper(
            runs.cancel,
        )
        self.create_with_run = async_to_streamed_response_wrapper(
            runs.create_with_run,
        )
        self.submit_tool_outputs = async_to_streamed_response_wrapper(
            runs.submit_tool_outputs,
        )

    @cached_property
    def steps(self) -> AsyncStepsResourceWithStreamingResponse:
        return AsyncStepsResourceWithStreamingResponse(self._runs.steps)
