# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List
from typing_extensions import Literal

import httpx

from ..types import response_create_params, response_retrieve_params, response_list_input_items_params
from .._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.response import Response
from ..types.conversations.includable import Includable
from ..types.response_list_input_items_response import ResponseListInputItemsResponse

__all__ = ["ResponsesResource", "AsyncResponsesResource"]


class ResponsesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ResponsesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return ResponsesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResponsesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return ResponsesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        body: response_create_params.Body,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """Creates a model response.

        Provide [text](https://main.excai.ai/docs/guides/text)
        or [image](https://main.excai.ai/docs/guides/images) inputs to generate
        [text](https://main.excai.ai/docs/guides/text) or
        [JSON](https://main.excai.ai/docs/guides/structured-outputs) outputs. Have the
        model call your own
        [custom code](https://main.excai.ai/docs/guides/function-calling) or use
        built-in [tools](https://main.excai.ai/docs/guides/tools) like
        [web search](https://main.excai.ai/docs/guides/tools-web-search) or
        [file search](https://main.excai.ai/docs/guides/tools-file-search) to use your
        own data as input for the model's response.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/responses",
            body=maybe_transform(body, response_create_params.ResponseCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Response,
        )

    def retrieve(
        self,
        response_id: str,
        *,
        include: List[Includable] | Omit = omit,
        include_obfuscation: bool | Omit = omit,
        starting_after: int | Omit = omit,
        stream: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """
        Retrieves a model response with the given ID.

        Args:
          include: Additional fields to include in the response. See the `include` parameter for
              Response creation above for more information.

          include_obfuscation: When true, stream obfuscation will be enabled. Stream obfuscation adds random
              characters to an `obfuscation` field on streaming delta events to normalize
              payload sizes as a mitigation to certain side-channel attacks. These obfuscation
              fields are included by default, but add a small amount of overhead to the data
              stream. You can set `include_obfuscation` to false to optimize for bandwidth if
              you trust the network links between your application and the EXCai API.

          starting_after: The sequence number of the event after which to start streaming.

          stream: If set to true, the model response data will be streamed to the client as it is
              generated using
              [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format).
              See the
              [Streaming section below](https://main.excai.ai/docs/api-reference/responses-streaming)
              for more information.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return self._get(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "include": include,
                        "include_obfuscation": include_obfuscation,
                        "starting_after": starting_after,
                        "stream": stream,
                    },
                    response_retrieve_params.ResponseRetrieveParams,
                ),
            ),
            cast_to=Response,
        )

    def delete(
        self,
        response_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Deletes a model response with the given ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def cancel(
        self,
        response_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """Cancels a model response with the given ID.

        Only responses created with the
        `background` parameter set to `true` can be cancelled.
        [Learn more](https://main.excai.ai/docs/guides/background).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return self._post(
            f"/responses/{response_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Response,
        )

    def list_input_items(
        self,
        response_id: str,
        *,
        after: str | Omit = omit,
        include: List[Includable] | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResponseListInputItemsResponse:
        """
        Returns a list of input items for a given response.

        Args:
          after: An item ID to list items after, used in pagination.

          include: Additional fields to include in the response. See the `include` parameter for
              Response creation above for more information.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: The order to return the input items in. Default is `desc`.

              - `asc`: Return the input items in ascending order.
              - `desc`: Return the input items in descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return self._get(
            f"/responses/{response_id}/input_items",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "include": include,
                        "limit": limit,
                        "order": order,
                    },
                    response_list_input_items_params.ResponseListInputItemsParams,
                ),
            ),
            cast_to=ResponseListInputItemsResponse,
        )


class AsyncResponsesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncResponsesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncResponsesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResponsesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncResponsesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        body: response_create_params.Body,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """Creates a model response.

        Provide [text](https://main.excai.ai/docs/guides/text)
        or [image](https://main.excai.ai/docs/guides/images) inputs to generate
        [text](https://main.excai.ai/docs/guides/text) or
        [JSON](https://main.excai.ai/docs/guides/structured-outputs) outputs. Have the
        model call your own
        [custom code](https://main.excai.ai/docs/guides/function-calling) or use
        built-in [tools](https://main.excai.ai/docs/guides/tools) like
        [web search](https://main.excai.ai/docs/guides/tools-web-search) or
        [file search](https://main.excai.ai/docs/guides/tools-file-search) to use your
        own data as input for the model's response.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/responses",
            body=await async_maybe_transform(body, response_create_params.ResponseCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Response,
        )

    async def retrieve(
        self,
        response_id: str,
        *,
        include: List[Includable] | Omit = omit,
        include_obfuscation: bool | Omit = omit,
        starting_after: int | Omit = omit,
        stream: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """
        Retrieves a model response with the given ID.

        Args:
          include: Additional fields to include in the response. See the `include` parameter for
              Response creation above for more information.

          include_obfuscation: When true, stream obfuscation will be enabled. Stream obfuscation adds random
              characters to an `obfuscation` field on streaming delta events to normalize
              payload sizes as a mitigation to certain side-channel attacks. These obfuscation
              fields are included by default, but add a small amount of overhead to the data
              stream. You can set `include_obfuscation` to false to optimize for bandwidth if
              you trust the network links between your application and the EXCai API.

          starting_after: The sequence number of the event after which to start streaming.

          stream: If set to true, the model response data will be streamed to the client as it is
              generated using
              [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#Event_stream_format).
              See the
              [Streaming section below](https://main.excai.ai/docs/api-reference/responses-streaming)
              for more information.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return await self._get(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "include": include,
                        "include_obfuscation": include_obfuscation,
                        "starting_after": starting_after,
                        "stream": stream,
                    },
                    response_retrieve_params.ResponseRetrieveParams,
                ),
            ),
            cast_to=Response,
        )

    async def delete(
        self,
        response_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Deletes a model response with the given ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def cancel(
        self,
        response_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Response:
        """Cancels a model response with the given ID.

        Only responses created with the
        `background` parameter set to `true` can be cancelled.
        [Learn more](https://main.excai.ai/docs/guides/background).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return await self._post(
            f"/responses/{response_id}/cancel",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Response,
        )

    async def list_input_items(
        self,
        response_id: str,
        *,
        after: str | Omit = omit,
        include: List[Includable] | Omit = omit,
        limit: int | Omit = omit,
        order: Literal["asc", "desc"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ResponseListInputItemsResponse:
        """
        Returns a list of input items for a given response.

        Args:
          after: An item ID to list items after, used in pagination.

          include: Additional fields to include in the response. See the `include` parameter for
              Response creation above for more information.

          limit: A limit on the number of objects to be returned. Limit can range between 1 and
              100, and the default is 20.

          order: The order to return the input items in. Default is `desc`.

              - `asc`: Return the input items in ascending order.
              - `desc`: Return the input items in descending order.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return await self._get(
            f"/responses/{response_id}/input_items",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "include": include,
                        "limit": limit,
                        "order": order,
                    },
                    response_list_input_items_params.ResponseListInputItemsParams,
                ),
            ),
            cast_to=ResponseListInputItemsResponse,
        )


class ResponsesResourceWithRawResponse:
    def __init__(self, responses: ResponsesResource) -> None:
        self._responses = responses

        self.create = to_raw_response_wrapper(
            responses.create,
        )
        self.retrieve = to_raw_response_wrapper(
            responses.retrieve,
        )
        self.delete = to_raw_response_wrapper(
            responses.delete,
        )
        self.cancel = to_raw_response_wrapper(
            responses.cancel,
        )
        self.list_input_items = to_raw_response_wrapper(
            responses.list_input_items,
        )


class AsyncResponsesResourceWithRawResponse:
    def __init__(self, responses: AsyncResponsesResource) -> None:
        self._responses = responses

        self.create = async_to_raw_response_wrapper(
            responses.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            responses.retrieve,
        )
        self.delete = async_to_raw_response_wrapper(
            responses.delete,
        )
        self.cancel = async_to_raw_response_wrapper(
            responses.cancel,
        )
        self.list_input_items = async_to_raw_response_wrapper(
            responses.list_input_items,
        )


class ResponsesResourceWithStreamingResponse:
    def __init__(self, responses: ResponsesResource) -> None:
        self._responses = responses

        self.create = to_streamed_response_wrapper(
            responses.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            responses.retrieve,
        )
        self.delete = to_streamed_response_wrapper(
            responses.delete,
        )
        self.cancel = to_streamed_response_wrapper(
            responses.cancel,
        )
        self.list_input_items = to_streamed_response_wrapper(
            responses.list_input_items,
        )


class AsyncResponsesResourceWithStreamingResponse:
    def __init__(self, responses: AsyncResponsesResource) -> None:
        self._responses = responses

        self.create = async_to_streamed_response_wrapper(
            responses.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            responses.retrieve,
        )
        self.delete = async_to_streamed_response_wrapper(
            responses.delete,
        )
        self.cancel = async_to_streamed_response_wrapper(
            responses.cancel,
        )
        self.list_input_items = async_to_streamed_response_wrapper(
            responses.list_input_items,
        )
