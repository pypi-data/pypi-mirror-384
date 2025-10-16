# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal

import httpx

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
from ...types.chat import (
    completion_list_params,
    completion_create_params,
    completion_update_params,
    completion_get_messages_params,
)
from ..._base_client import make_request_options
from ...types.chat.metadata_param import MetadataParam
from ...types.chat.create_response import CreateResponse
from ...types.chat.completion_list_response import CompletionListResponse
from ...types.chat.completion_delete_response import CompletionDeleteResponse
from ...types.chat.completion_get_messages_response import CompletionGetMessagesResponse

__all__ = ["CompletionsResource", "AsyncCompletionsResource"]


class CompletionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CompletionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return CompletionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CompletionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return CompletionsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        body: completion_create_params.Body,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """
        **Starting a new project?** We recommend trying
        [Responses](https://main.excai.ai/docs/api-reference/responses) to take
        advantage of the latest EXCai platform features. Compare
        [Chat Completions with Responses](https://main.excai.ai/docs/guides/responses-vs-chat-completions?api-mode=responses).

        ---

        Creates a model response for the given chat conversation. Learn more in the
        [text generation](https://main.excai.ai/docs/guides/text-generation),
        [vision](https://main.excai.ai/docs/guides/vision), and
        [audio](https://main.excai.ai/docs/guides/audio) guides.

        Parameter support can differ depending on the model used to generate the
        response, particularly for newer reasoning models. Parameters that are only
        supported for reasoning models are noted below. For the current state of
        unsupported parameters in reasoning models,
        [refer to the reasoning guide](https://main.excai.ai/docs/guides/reasoning).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/chat/completions",
            body=maybe_transform(body, completion_create_params.CompletionCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    def retrieve(
        self,
        completion_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """Get a stored chat completion.

        Only Chat Completions that have been created with
        the `store` parameter set to `true` will be returned.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return self._get(
            f"/chat/completions/{completion_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    def update(
        self,
        completion_id: str,
        *,
        metadata: Optional[MetadataParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """Modify a stored chat completion.

        Only Chat Completions that have been created
        with the `store` parameter set to `true` can be modified. Currently, the only
        supported modification is to update the `metadata` field.

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
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return self._post(
            f"/chat/completions/{completion_id}",
            body=maybe_transform({"metadata": metadata}, completion_update_params.CompletionUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: str | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionListResponse:
        """List stored Chat Completions.

        Only Chat Completions that have been stored with
        the `store` parameter set to `true` will be returned.

        Args:
          after: Identifier for the last chat completion from the previous pagination request.

          limit: Number of Chat Completions to retrieve.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The model used to generate the Chat Completions.

          order: Sort order for Chat Completions by timestamp. Use `asc` for ascending order or
              `desc` for descending order. Defaults to `asc`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/chat/completions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "metadata": metadata,
                        "model": model,
                        "order": order,
                    },
                    completion_list_params.CompletionListParams,
                ),
            ),
            cast_to=CompletionListResponse,
        )

    def delete(
        self,
        completion_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionDeleteResponse:
        """Delete a stored chat completion.

        Only Chat Completions that have been created
        with the `store` parameter set to `true` can be deleted.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return self._delete(
            f"/chat/completions/{completion_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompletionDeleteResponse,
        )

    def get_messages(
        self,
        completion_id: str,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionGetMessagesResponse:
        """Get the messages in a stored chat completion.

        Only Chat Completions that have
        been created with the `store` parameter set to `true` will be returned.

        Args:
          after: Identifier for the last message from the previous pagination request.

          limit: Number of messages to retrieve.

          order: Sort order for messages by timestamp. Use `asc` for ascending order or `desc`
              for descending order. Defaults to `asc`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return self._get(
            f"/chat/completions/{completion_id}/messages",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "order": order,
                    },
                    completion_get_messages_params.CompletionGetMessagesParams,
                ),
            ),
            cast_to=CompletionGetMessagesResponse,
        )


class AsyncCompletionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCompletionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCompletionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCompletionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncCompletionsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        body: completion_create_params.Body,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """
        **Starting a new project?** We recommend trying
        [Responses](https://main.excai.ai/docs/api-reference/responses) to take
        advantage of the latest EXCai platform features. Compare
        [Chat Completions with Responses](https://main.excai.ai/docs/guides/responses-vs-chat-completions?api-mode=responses).

        ---

        Creates a model response for the given chat conversation. Learn more in the
        [text generation](https://main.excai.ai/docs/guides/text-generation),
        [vision](https://main.excai.ai/docs/guides/vision), and
        [audio](https://main.excai.ai/docs/guides/audio) guides.

        Parameter support can differ depending on the model used to generate the
        response, particularly for newer reasoning models. Parameters that are only
        supported for reasoning models are noted below. For the current state of
        unsupported parameters in reasoning models,
        [refer to the reasoning guide](https://main.excai.ai/docs/guides/reasoning).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/chat/completions",
            body=await async_maybe_transform(body, completion_create_params.CompletionCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    async def retrieve(
        self,
        completion_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """Get a stored chat completion.

        Only Chat Completions that have been created with
        the `store` parameter set to `true` will be returned.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return await self._get(
            f"/chat/completions/{completion_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    async def update(
        self,
        completion_id: str,
        *,
        metadata: Optional[MetadataParam],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CreateResponse:
        """Modify a stored chat completion.

        Only Chat Completions that have been created
        with the `store` parameter set to `true` can be modified. Currently, the only
        supported modification is to update the `metadata` field.

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
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return await self._post(
            f"/chat/completions/{completion_id}",
            body=await async_maybe_transform({"metadata": metadata}, completion_update_params.CompletionUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CreateResponse,
        )

    async def list(
        self,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        metadata: Optional[MetadataParam] | Omit = omit,
        model: str | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionListResponse:
        """List stored Chat Completions.

        Only Chat Completions that have been stored with
        the `store` parameter set to `true` will be returned.

        Args:
          after: Identifier for the last chat completion from the previous pagination request.

          limit: Number of Chat Completions to retrieve.

          metadata: Set of 16 key-value pairs that can be attached to an object. This can be useful
              for storing additional information about the object in a structured format, and
              querying for objects via API or the dashboard.

              Keys are strings with a maximum length of 64 characters. Values are strings with
              a maximum length of 512 characters.

          model: The model used to generate the Chat Completions.

          order: Sort order for Chat Completions by timestamp. Use `asc` for ascending order or
              `desc` for descending order. Defaults to `asc`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/chat/completions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "metadata": metadata,
                        "model": model,
                        "order": order,
                    },
                    completion_list_params.CompletionListParams,
                ),
            ),
            cast_to=CompletionListResponse,
        )

    async def delete(
        self,
        completion_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionDeleteResponse:
        """Delete a stored chat completion.

        Only Chat Completions that have been created
        with the `store` parameter set to `true` can be deleted.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return await self._delete(
            f"/chat/completions/{completion_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CompletionDeleteResponse,
        )

    async def get_messages(
        self,
        completion_id: str,
        *,
        after: str | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CompletionGetMessagesResponse:
        """Get the messages in a stored chat completion.

        Only Chat Completions that have
        been created with the `store` parameter set to `true` will be returned.

        Args:
          after: Identifier for the last message from the previous pagination request.

          limit: Number of messages to retrieve.

          order: Sort order for messages by timestamp. Use `asc` for ascending order or `desc`
              for descending order. Defaults to `asc`.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not completion_id:
            raise ValueError(f"Expected a non-empty value for `completion_id` but received {completion_id!r}")
        return await self._get(
            f"/chat/completions/{completion_id}/messages",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "limit": limit,
                        "order": order,
                    },
                    completion_get_messages_params.CompletionGetMessagesParams,
                ),
            ),
            cast_to=CompletionGetMessagesResponse,
        )


class CompletionsResourceWithRawResponse:
    def __init__(self, completions: CompletionsResource) -> None:
        self._completions = completions

        self.create = to_raw_response_wrapper(
            completions.create,
        )
        self.retrieve = to_raw_response_wrapper(
            completions.retrieve,
        )
        self.update = to_raw_response_wrapper(
            completions.update,
        )
        self.list = to_raw_response_wrapper(
            completions.list,
        )
        self.delete = to_raw_response_wrapper(
            completions.delete,
        )
        self.get_messages = to_raw_response_wrapper(
            completions.get_messages,
        )


class AsyncCompletionsResourceWithRawResponse:
    def __init__(self, completions: AsyncCompletionsResource) -> None:
        self._completions = completions

        self.create = async_to_raw_response_wrapper(
            completions.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            completions.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            completions.update,
        )
        self.list = async_to_raw_response_wrapper(
            completions.list,
        )
        self.delete = async_to_raw_response_wrapper(
            completions.delete,
        )
        self.get_messages = async_to_raw_response_wrapper(
            completions.get_messages,
        )


class CompletionsResourceWithStreamingResponse:
    def __init__(self, completions: CompletionsResource) -> None:
        self._completions = completions

        self.create = to_streamed_response_wrapper(
            completions.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            completions.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            completions.update,
        )
        self.list = to_streamed_response_wrapper(
            completions.list,
        )
        self.delete = to_streamed_response_wrapper(
            completions.delete,
        )
        self.get_messages = to_streamed_response_wrapper(
            completions.get_messages,
        )


class AsyncCompletionsResourceWithStreamingResponse:
    def __init__(self, completions: AsyncCompletionsResource) -> None:
        self._completions = completions

        self.create = async_to_streamed_response_wrapper(
            completions.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            completions.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            completions.update,
        )
        self.list = async_to_streamed_response_wrapper(
            completions.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            completions.delete,
        )
        self.get_messages = async_to_streamed_response_wrapper(
            completions.get_messages,
        )
