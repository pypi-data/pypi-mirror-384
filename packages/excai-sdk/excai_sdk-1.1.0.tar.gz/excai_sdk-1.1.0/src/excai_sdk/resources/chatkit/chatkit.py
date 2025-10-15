# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, Mapping, cast

import httpx

from ...types import chatkit_upload_file_params
from .threads import (
    ThreadsResource,
    AsyncThreadsResource,
    ThreadsResourceWithRawResponse,
    AsyncThreadsResourceWithRawResponse,
    ThreadsResourceWithStreamingResponse,
    AsyncThreadsResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NotGiven, FileTypes, not_given
from ..._utils import extract_files, maybe_transform, deepcopy_minimal, async_maybe_transform
from .sessions import (
    SessionsResource,
    AsyncSessionsResource,
    SessionsResourceWithRawResponse,
    AsyncSessionsResourceWithRawResponse,
    SessionsResourceWithStreamingResponse,
    AsyncSessionsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.chatkit_upload_file_response import ChatkitUploadFileResponse

__all__ = ["ChatkitResource", "AsyncChatkitResource"]


class ChatkitResource(SyncAPIResource):
    @cached_property
    def sessions(self) -> SessionsResource:
        return SessionsResource(self._client)

    @cached_property
    def threads(self) -> ThreadsResource:
        return ThreadsResource(self._client)

    @cached_property
    def with_raw_response(self) -> ChatkitResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return ChatkitResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ChatkitResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return ChatkitResourceWithStreamingResponse(self)

    def upload_file(
        self,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatkitUploadFileResponse:
        """
        Upload a ChatKit file

        Args:
          file: Binary file contents to store with the ChatKit session. Supports PDFs and PNG,
              JPG, JPEG, GIF, or WEBP images.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        if files:
            # It should be noted that the actual Content-Type header that will be
            # sent to the server will contain a `boundary` parameter, e.g.
            # multipart/form-data; boundary=---abc--
            extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return cast(
            ChatkitUploadFileResponse,
            self._post(
                "/chatkit/files",
                body=maybe_transform(body, chatkit_upload_file_params.ChatkitUploadFileParams),
                files=files,
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ChatkitUploadFileResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class AsyncChatkitResource(AsyncAPIResource):
    @cached_property
    def sessions(self) -> AsyncSessionsResource:
        return AsyncSessionsResource(self._client)

    @cached_property
    def threads(self) -> AsyncThreadsResource:
        return AsyncThreadsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncChatkitResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/malkhenizan/excai-python#accessing-raw-response-data-eg-headers
        """
        return AsyncChatkitResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncChatkitResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/malkhenizan/excai-python#with_streaming_response
        """
        return AsyncChatkitResourceWithStreamingResponse(self)

    async def upload_file(
        self,
        *,
        file: FileTypes,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ChatkitUploadFileResponse:
        """
        Upload a ChatKit file

        Args:
          file: Binary file contents to store with the ChatKit session. Supports PDFs and PNG,
              JPG, JPEG, GIF, or WEBP images.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        body = deepcopy_minimal({"file": file})
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        if files:
            # It should be noted that the actual Content-Type header that will be
            # sent to the server will contain a `boundary` parameter, e.g.
            # multipart/form-data; boundary=---abc--
            extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return cast(
            ChatkitUploadFileResponse,
            await self._post(
                "/chatkit/files",
                body=await async_maybe_transform(body, chatkit_upload_file_params.ChatkitUploadFileParams),
                files=files,
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, ChatkitUploadFileResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class ChatkitResourceWithRawResponse:
    def __init__(self, chatkit: ChatkitResource) -> None:
        self._chatkit = chatkit

        self.upload_file = to_raw_response_wrapper(
            chatkit.upload_file,
        )

    @cached_property
    def sessions(self) -> SessionsResourceWithRawResponse:
        return SessionsResourceWithRawResponse(self._chatkit.sessions)

    @cached_property
    def threads(self) -> ThreadsResourceWithRawResponse:
        return ThreadsResourceWithRawResponse(self._chatkit.threads)


class AsyncChatkitResourceWithRawResponse:
    def __init__(self, chatkit: AsyncChatkitResource) -> None:
        self._chatkit = chatkit

        self.upload_file = async_to_raw_response_wrapper(
            chatkit.upload_file,
        )

    @cached_property
    def sessions(self) -> AsyncSessionsResourceWithRawResponse:
        return AsyncSessionsResourceWithRawResponse(self._chatkit.sessions)

    @cached_property
    def threads(self) -> AsyncThreadsResourceWithRawResponse:
        return AsyncThreadsResourceWithRawResponse(self._chatkit.threads)


class ChatkitResourceWithStreamingResponse:
    def __init__(self, chatkit: ChatkitResource) -> None:
        self._chatkit = chatkit

        self.upload_file = to_streamed_response_wrapper(
            chatkit.upload_file,
        )

    @cached_property
    def sessions(self) -> SessionsResourceWithStreamingResponse:
        return SessionsResourceWithStreamingResponse(self._chatkit.sessions)

    @cached_property
    def threads(self) -> ThreadsResourceWithStreamingResponse:
        return ThreadsResourceWithStreamingResponse(self._chatkit.threads)


class AsyncChatkitResourceWithStreamingResponse:
    def __init__(self, chatkit: AsyncChatkitResource) -> None:
        self._chatkit = chatkit

        self.upload_file = async_to_streamed_response_wrapper(
            chatkit.upload_file,
        )

    @cached_property
    def sessions(self) -> AsyncSessionsResourceWithStreamingResponse:
        return AsyncSessionsResourceWithStreamingResponse(self._chatkit.sessions)

    @cached_property
    def threads(self) -> AsyncThreadsResourceWithStreamingResponse:
        return AsyncThreadsResourceWithStreamingResponse(self._chatkit.threads)
